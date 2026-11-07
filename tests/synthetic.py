"""Deterministic test recording; these signals do not establish human EEG accuracy."""
from dataclasses import asdict

import numpy as np

from calibration_session import build_protocol, marker_name
from eog_pipeline import CHANNELS, Recording


def make_session(repetitions=3, sfreq=100):
    protocol = build_protocol(repetitions=repetitions)
    duration = sum(p["duration_sec"] for p in protocol)
    times = np.arange(round(duration * sfreq)) / sfreq
    rng = np.random.default_rng(42)
    h = np.full(len(times), 20.0)
    v = np.full(len(times), 35.0)
    events = []
    start = 0.0
    for i, trial in enumerate(protocol):
        stop = start + trial["duration_sec"]
        mask = (times >= start) & (times < stop)
        local = times[mask] - start
        label = trial["label"]
        # Deliberately reverse the sign assumptions in the original scripts.
        if label == "RIGHT":
            h[mask] -= 80
        elif label == "LEFT":
            h[mask] += 90
        elif label == "UP":
            v[mask] -= 60
        elif label == "DOWN":
            v[mask] += 75
        elif label == "BLINK":
            v[mask] += 600 * np.exp(-0.5 * ((local % 1 - 0.5) / 0.06) ** 2)
        events.append({**trial, "trial_id": str(i), "onset_sec": start,
                       "marker": marker_name("synthetic", str(i), label)})
        start = stop
    data_uv = np.stack((100 - (h - 20) / 2, 120 + (h - 20) / 2, v + 5, v - 5))
    data_uv += rng.normal(0, 0.2, data_uv.shape)
    metadata = {"path": "synthetic", "format": "synthetic",
                "channels": dict(zip(CHANNELS, CHANNELS)), "sfreq_hz": sfreq,
                "samples": len(times), "source_highpass_hz": 0,
                "source_lowpass_hz": sfreq / 2}
    recording = Recording(data_uv * 1e-6, float(sfreq), metadata, [])
    session = {"schema_version": 1, "session_id": "synthetic", "status": "complete",
               "events": events, "end_marker": marker_name("synthetic", "END", "END"),
               "screen": {"width_px": 1000, "height_px": 700}}
    return recording, session


def write_edf(recording, path):
    """Write a small plain EDF fixture without adding an EDF export dependency."""
    from pathlib import Path

    sfreq = int(recording.sfreq)
    if sfreq != recording.sfreq or recording.data.shape[1] % sfreq:
        raise ValueError("Demo EDF requires integer Hz and complete one-second records.")
    nrecords = recording.data.shape[1] // sfreq
    def field(value, width):
        encoded = str(value).encode("ascii")
        if len(encoded) > width:
            raise ValueError("EDF field is too long.")
        return encoded.ljust(width, b" ")
    header = b"".join([
        field("0", 8), field("Synthetic fixture", 80),
        field("Synthetic EOG software test only", 80), field("01.01.26", 8),
        field("00.00.00", 8), field(256 + 256 * 4, 8), field("", 44),
        field(nrecords, 8), field(1, 8), field(4, 4),
    ])
    channel_fields = [
        (CHANNELS, 16), ([""] * 4, 80), (["uV"] * 4, 8),
        ([-1000] * 4, 8), ([1000] * 4, 8), ([-32768] * 4, 8),
        ([32767] * 4, 8), ([""] * 4, 80), ([sfreq] * 4, 8), ([""] * 4, 32),
    ]
    header += b"".join(field(value, width) for values, width in channel_fields
                       for value in values)
    physical = recording.data * 1e6
    if np.max(np.abs(physical)) >= 1000:
        raise ValueError("Synthetic signals exceed EDF physical range.")
    digital = np.round((physical + 1000) / 2000 * 65535 - 32768)
    digital = digital.reshape(4, nrecords, sfreq).transpose(1, 0, 2).astype("<i2")
    Path(path).write_bytes(header + digital.tobytes())


if __name__ == "__main__":
    import argparse
    from pathlib import Path
    from eog_pipeline import write_json

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="output/demo")
    args = parser.parse_args()
    directory = Path(args.output)
    if directory.exists():
        parser.error("Choose a new output directory; demo files are never overwritten.")
    directory.mkdir(parents=True)
    recording, session = make_session()
    session["synthetic_test_fixture"] = True
    write_edf(recording, directory / "recording.edf")
    write_json(directory / "session.json", session)
    print(f"Synthetic software-test recording and session saved to {directory}")
