"""Shared causal EOG processing, recording I/O, calibration schema and dwell logic."""
from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Iterator

import numpy as np
from scipy.signal import butter, sosfilt, sosfilt_zi

SCHEMA_VERSION = 1
PROCESSING_VERSION = "causal-eog-v1"
CHANNELS = ("F7", "F8", "Fp1", "Fp2")
DIRECTIONS = ("RIGHT", "LEFT", "UP", "DOWN")
LABELS = ("CENTER", *DIRECTIONS, "BLINK")


def finite_number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value):
        raise ValueError(f"{name} must be a finite number.")
    return float(value)


@dataclass(frozen=True)
class ProcessingConfig:
    # Low-pass only preserves sustained offsets; center subtraction removes baseline.
    # An optional high-pass changes the model and requires a new calibration.
    lowpass_hz: float = 5.0
    highpass_hz: float | None = None
    filter_order: int = 4
    warmup_sec: float = 2.0
    window_sec: float = 3.0
    recent_sec: float = 0.2
    step_sec: float = 0.1
    dwell_sec: float = 3.0
    gap_sec: float = 0.05
    hysteresis_ratio: float = 0.8

    def validate(self, sfreq):
        sfreq = finite_number(sfreq, "Sampling frequency")
        if sfreq <= 0:
            raise ValueError("Sampling frequency must be positive.")
        for name in ("lowpass_hz", "window_sec", "recent_sec", "step_sec",
                     "dwell_sec", "gap_sec"):
            if finite_number(getattr(self, name), name) <= 0:
                raise ValueError(f"{name} must be positive.")
        if finite_number(self.warmup_sec, "warmup_sec") < 0:
            raise ValueError("warmup_sec cannot be negative.")
        if not isinstance(self.filter_order, int) or not 1 <= self.filter_order <= 8:
            raise ValueError("filter_order must be an integer between 1 and 8.")
        if not 0 < finite_number(self.hysteresis_ratio, "hysteresis_ratio") <= 1:
            raise ValueError("hysteresis_ratio must be in (0, 1].")
        if self.lowpass_hz >= sfreq / 2:
            raise ValueError("Low-pass cutoff must be below Nyquist.")
        if self.highpass_hz is not None:
            if not 0 < finite_number(self.highpass_hz, "highpass_hz") < self.lowpass_hz:
                raise ValueError("High-pass cutoff must be between zero and low-pass.")
        if not self.step_sec <= self.recent_sec <= self.window_sec:
            raise ValueError("Require step_sec <= recent_sec <= window_sec.")
        if any(round(sfreq * x) < 1 for x in
               (self.window_sec, self.recent_sec, self.step_sec)):
            raise ValueError("Sampling frequency is too low for the selected windows.")
        if self.gap_sec < 1.5 / sfreq:
            raise ValueError("gap_sec must exceed 1.5 sample intervals.")
        return self


def write_json(path, payload):
    """Atomic checkpoint; refuse NaNs instead of producing invalid JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, allow_nan=False)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text + "\n", encoding="utf-8")
    temporary.replace(path)


def read_json(path):
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def channel_indices(names, mapping=None):
    mapping = mapping or {}
    if set(mapping) - set(CHANNELS):
        raise ValueError(f"Channel-map keys must be among {CHANNELS}.")
    normalized = {}
    for i, name in enumerate(names):
        normalized.setdefault(str(name).strip().casefold(), []).append(i)
    indices = []
    for canonical in CHANNELS:
        actual = mapping.get(canonical, canonical)
        matches = normalized.get(str(actual).strip().casefold(), [])
        if len(matches) != 1:
            raise ValueError(f"Need exactly one channel for {canonical} ({actual}); "
                             f"available channels: {list(names)}")
        indices.append(matches[0])
    if len(set(indices)) != len(CHANNELS):
        raise ValueError("The four required channels must be distinct.")
    return indices


@dataclass
class Recording:
    data: np.ndarray  # canonical channels x samples, volts
    sfreq: float
    metadata: dict
    annotations: list[dict]

    @property
    def duration(self):
        return self.data.shape[1] / self.sfreq


def load_recording(path, mapping=None):
    """Only read required channels; do not filter or rereference the source."""
    import mne

    path = Path(path)
    if not path.is_file():
        raise ValueError(f"Recording does not exist: {path}")
    extension = path.suffix.lower()
    if extension == ".cnt":
        raw = mne.io.read_raw_ant(path, preload=False, verbose=False)
    elif extension == ".edf":
        raw = mne.io.read_raw_edf(path, preload=False, verbose=False)
    else:
        raise ValueError("Supported recording formats are ANT CNT and EDF.")
    try:
        indices = channel_indices(raw.ch_names, mapping)
        bad = [raw.ch_names[i] for i in indices if raw.ch_names[i] in raw.info["bads"]]
        if bad:
            raise ValueError(f"Required channels marked bad: {bad}")
        data = raw.get_data(picks=indices, reject_by_annotation="NaN")
        annotations = [
            {"onset_sec": float(a["onset"] - raw.first_time),
             "duration_sec": float(a["duration"]),
             "description": str(a["description"])}
            for a in raw.annotations
        ]
        # Zero-duration impedance/edge markers are discontinuities, not valid gaze.
        for a in annotations:
            description = a["description"].casefold()
            if any(token in description for token in ("impedance", "edge", "bad_acq_skip")):
                start = max(0, int(round(a["onset_sec"] * raw.info["sfreq"])))
                stop = min(data.shape[1], max(start + 1, int(np.ceil(
                    (a["onset_sec"] + a["duration_sec"]) * raw.info["sfreq"]))))
                data[:, start:stop] = np.nan
        metadata = {
            "path": str(path.resolve()), "format": extension[1:],
            "channels": dict(zip(CHANNELS, [raw.ch_names[i] for i in indices])),
            "sfreq_hz": float(raw.info["sfreq"]), "samples": int(raw.n_times),
            "source_highpass_hz": float(raw.info["highpass"]),
            "source_lowpass_hz": float(raw.info["lowpass"]),
        }
        return Recording(data, float(raw.info["sfreq"]), metadata, annotations)
    finally:
        raw.close()


@dataclass
class Feature:
    time_sec: float
    generation: int
    quality: str
    mean_uv: list | None = None
    variance_uv2: list | None = None
    recent_mean_uv: list | None = None
    window_start_sec: float | None = None


class FeatureStream:
    """Identical output regardless of caller chunk sizes; gaps reset all history."""

    def __init__(self, sfreq, config=None):
        self.sfreq = float(sfreq)
        self.config = (config or ProcessingConfig()).validate(self.sfreq)
        cfg = self.config
        if cfg.highpass_hz is None:
            self.sos = butter(cfg.filter_order, cfg.lowpass_hz,
                              fs=self.sfreq, output="sos")
        else:
            self.sos = butter(cfg.filter_order, [cfg.highpass_hz, cfg.lowpass_hz],
                              btype="bandpass", fs=self.sfreq, output="sos")
        self.window_n = round(cfg.window_sec * self.sfreq)
        self.recent_n = round(cfg.recent_sec * self.sfreq)
        self.step_n = round(cfg.step_sec * self.sfreq)
        self.warmup_n = round(cfg.warmup_sec * self.sfreq)
        self.generation = -1
        self.reset()

    def reset(self):
        self.generation += 1
        self.zi = None
        self.history = deque(maxlen=self.window_n)
        self.seen = 0
        self.last_time = None

    def push(self, data, timestamps) -> Iterator[Feature]:
        data = np.asarray(data, dtype=float)
        timestamps = np.asarray(timestamps, dtype=float)
        if data.ndim != 2 or data.shape != (4, len(timestamps)):
            raise ValueError("Samples must have shape (4, number of timestamps).")
        if not len(timestamps):
            return
        if not np.isfinite(timestamps).all() or np.any(np.diff(timestamps) <= 0):
            raise ValueError("Sample timestamps must be finite and strictly increasing.")
        if self.last_time is not None and timestamps[0] <= self.last_time:
            raise ValueError("Samples arrived out of order; reconnect and reset.")
        valid = np.isfinite(data).all(axis=0)
        changes = np.flatnonzero(
            (valid[1:] != valid[:-1]) |
            (np.diff(timestamps) > self.config.gap_sec)
        ) + 1
        bounds = np.r_[0, changes, len(timestamps)]
        for first, stop in zip(bounds[:-1], bounds[1:]):
            times = timestamps[first:stop]
            if not valid[first]:
                self.reset()
                self.last_time = float(times[-1])
                yield Feature(float(times[-1]), self.generation, "INVALID")
                continue
            if self.last_time is not None and times[0] - self.last_time > self.config.gap_sec:
                self.reset()
                yield Feature(float(times[0]), self.generation, "GAP")
            block = data[:, first:stop] * 1e6
            axes = np.stack((block[1] - block[0], (block[2] + block[3]) / 2), axis=1)
            if self.zi is None:
                self.zi = sosfilt_zi(self.sos)[:, :, None] * axes[0][None, None, :]
            filtered, self.zi = sosfilt(self.sos, axes, axis=0, zi=self.zi)
            for values, timestamp in zip(filtered, times):
                self.seen += 1
                if self.seen > self.warmup_n:
                    self.history.append((float(timestamp), values))
                if self.seen % self.step_n:
                    continue
                if len(self.history) < self.window_n:
                    yield Feature(float(timestamp), self.generation, "WARMUP")
                    continue
                matrix = np.asarray([item[1] for item in self.history])
                yield Feature(
                    float(timestamp), self.generation, "OK",
                    np.mean(matrix, axis=0).tolist(), np.var(matrix, axis=0).tolist(),
                    np.mean(matrix[-self.recent_n:], axis=0).tolist(),
                    self.history[0][0],
                )
            self.last_time = float(times[-1])


def calibration_model(model):
    """Validate saved artifacts before they can drive a classifier."""
    if model.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported calibration schema; recalibrate.")
    if model.get("processing_version") != PROCESSING_VERSION:
        raise ValueError("Incompatible processing implementation; recalibrate.")
    config = ProcessingConfig(**model["processing"])
    config.validate(model["sfreq_hz"])
    if model.get("units") != {"amplitude": "uV", "variance": "uV^2"}:
        raise ValueError("Calibration units are missing or incompatible.")
    if not isinstance(model.get("reference"), str) or not model["reference"].strip():
        raise ValueError("Calibration must identify the acquisition reference.")
    if model.get("quality", {}).get("passed") is not True:
        raise ValueError("Calibration did not pass quality checks.")
    if len(model["baseline_uv"]) != 2 or len(model["variance_limits_uv2"]) != 2:
        raise ValueError("Expected two baseline and variance values.")
    for value in model["baseline_uv"]:
        finite_number(value, "Baseline")
    for value in model["variance_limits_uv2"]:
        if finite_number(value, "Variance limit") <= 0:
            raise ValueError("Variance limits must be positive.")
    if set(model["directions"]) != set(DIRECTIONS):
        raise ValueError("Calibration must contain all four directions.")
    for name, rule in model["directions"].items():
        if rule["axis"] != (0 if name in ("RIGHT", "LEFT") else 1):
            raise ValueError(f"Incorrect axis for {name}.")
        if rule["polarity"] not in (-1, 1):
            raise ValueError("Polarity must be +1 or -1.")
        if finite_number(rule["threshold_uv"], "Direction threshold") <= 0:
            raise ValueError("Direction thresholds must be positive.")
    for a, b in (("RIGHT", "LEFT"), ("UP", "DOWN")):
        if model["directions"][a]["polarity"] == model["directions"][b]["polarity"]:
            raise ValueError(f"{a} and {b} must have opposite polarity.")
    return model


def check_compatibility(model, sfreq, reference):
    calibration_model(model)
    if not np.isclose(sfreq, model["sfreq_hz"], rtol=0, atol=1e-6):
        raise ValueError(f"Sampling rate {sfreq} does not match calibration "
                         f"{model['sfreq_hz']}; recollect or recalibrate.")
    if reference.strip().casefold() != model["reference"].strip().casefold():
        raise ValueError("Acquisition reference differs from calibration.")


def direction_for(mean_uv, model, previous=None):
    centered = np.asarray(mean_uv) - model["baseline_uv"]
    matches = []
    for label, rule in model["directions"].items():
        threshold = rule["threshold_uv"]
        if previous == label:
            threshold *= model["processing"]["hysteresis_ratio"]
        if centered[rule["axis"]] * rule["polarity"] > threshold:
            matches.append(label)
    if len(matches) > 1:
        return "AMBIGUOUS"
    return matches[0] if matches else "CENTER"


def candidate_for(feature, model, previous=None, recent=False):
    if feature.quality != "OK":
        return feature.quality
    if np.any(np.asarray(feature.variance_uv2) > model["variance_limits_uv2"]):
        return "TRANSITION_BLINK"
    return direction_for(feature.recent_mean_uv if recent else feature.mean_uv,
                         model, previous)


class DwellClassifier:
    """Require uninterrupted eligible evidence; never bridge blinks or missing data."""

    def __init__(self, model):
        self.model = calibration_model(model)
        self.config = ProcessingConfig(**model["processing"])
        self.reset()

    def reset(self):
        self.candidate = None
        self.since = None
        self.last_time = None
        self.generation = None
        self.active = None

    def update(self, feature):
        if (self.generation != feature.generation or
                (self.last_time is not None and
                 feature.time_sec - self.last_time > self.config.step_sec * 2.5)):
            self.reset()
        candidate = candidate_for(feature, self.model, self.candidate)
        recent = candidate_for(feature, self.model, self.candidate, recent=True)
        if candidate in DIRECTIONS and recent != candidate:
            candidate = "TRANSITION"
        if candidate in DIRECTIONS:
            if candidate != self.candidate:
                self.since = feature.time_sec
                self.active = None
            elapsed = max(0.0, feature.time_sec - self.since)
            activated = elapsed + 1e-9 >= self.config.dwell_sec
            state = candidate if activated else "DWELLING"
            activation = activated and self.active != candidate
            self.active = candidate if activated else None
            self.candidate = candidate
        else:
            self.candidate = self.since = self.active = None
            elapsed = 0.0
            state = candidate
            activation = False
        self.last_time = feature.time_sec
        self.generation = feature.generation
        return {
            "time_sec": feature.time_sec, "quality": feature.quality,
            "candidate": candidate, "state": state,
            "dwell_sec": min(elapsed, self.config.dwell_sec),
            "activated": activation,
            "h_mean_uv": feature.mean_uv[0] if feature.mean_uv else None,
            "v_mean_uv": feature.mean_uv[1] if feature.mean_uv else None,
            "h_variance_uv2": feature.variance_uv2[0] if feature.variance_uv2 else None,
            "v_variance_uv2": feature.variance_uv2[1] if feature.variance_uv2 else None,
        }


def analyze_recording(recording, config):
    stream = FeatureStream(recording.sfreq, config)
    # This also exercises the streaming path without loading/filtering future data.
    chunk_n = max(1, round(recording.sfreq))
    for start in range(0, recording.data.shape[1], chunk_n):
        stop = min(start + chunk_n, recording.data.shape[1])
        yield from stream.push(recording.data[:, start:stop],
                               np.arange(start, stop) / recording.sfreq)

