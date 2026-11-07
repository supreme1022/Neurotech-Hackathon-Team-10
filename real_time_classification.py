"""Classify ANT CNT/EDF playback or an existing LSL EEG stream using saved calibration."""
from __future__ import annotations

import argparse
from collections import Counter, deque
from datetime import datetime
from pathlib import Path
import csv
import time

import numpy as np

from eog_pipeline import (
    DwellClassifier, Feature, FeatureStream, ProcessingConfig, analyze_recording,
    calibration_model, check_compatibility, finite_number, load_recording,
    read_json, write_json,
)

RESULT_FIELDS = (
    "time_sec", "quality", "candidate", "state", "dwell_sec", "activated",
    "h_mean_uv", "v_mean_uv", "h_variance_uv2", "v_variance_uv2",
)


class ResultSink:
    def __init__(self, path, model, source, plot=False):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = self.path.open("x", newline="", encoding="utf-8")
        self.writer = csv.DictWriter(self.handle, fieldnames=RESULT_FIELDS)
        self.writer.writeheader()
        self.model = model
        self.source = source
        self.counts = Counter()
        self.activations = Counter()
        self.rows = 0
        self.last_state = None
        self.last_print = -np.inf
        self.plot = None
        if plot:
            import matplotlib.pyplot as plt
            plt.ion()
            self.plot = plt
            self.fig, self.axes = plt.subplots(2, 1, sharex=True, figsize=(11, 7))
            self.fig.canvas.manager.set_window_title("EOG gaze classification")
            self.history = deque(maxlen=100)
            self.lines = [ax.plot([], [])[0] for ax in self.axes]
            for i, ax in enumerate(self.axes):
                ax.set_ylabel(("Horizontal" if i == 0 else "Vertical") + " mean (uV)")
                for rule in model["directions"].values():
                    if rule["axis"] == i:
                        ax.axhline(model["baseline_uv"][i] +
                                   rule["threshold_uv"] * rule["polarity"],
                                   linestyle="--", color="gray")
                ax.grid(alpha=0.2)
            self.axes[-1].set_xlabel("Recording / stream time (seconds)")
            self.fig.tight_layout(rect=[0, 0, 1, 0.9])

    def emit(self, result):
        self.writer.writerow(result)
        self.handle.flush()
        self.rows += 1
        self.counts[result["state"]] += 1
        if result["activated"]:
            self.activations[result["state"]] += 1
        if (result["state"] != self.last_state or
                result["time_sec"] - self.last_print >= 1.0):
            print(f"{result['time_sec']:8.2f}s | {result['state']:18} | "
                  f"candidate={result['candidate']:16} | "
                  f"dwell={result['dwell_sec']:.1f}/{self.model['processing']['dwell_sec']:g}s | "
                  f"quality={result['quality']}")
            self.last_state = result["state"]
            self.last_print = result["time_sec"]
        if self.plot is not None:
            if not self.plot.fignum_exists(self.fig.number):
                raise KeyboardInterrupt
            if result["h_mean_uv"] is None:
                self.history.clear()
            else:
                self.history.append(result)
            if self.history:
                times = [r["time_sec"] for r in self.history]
                for line, ax, key in zip(
                        self.lines, self.axes, ("h_mean_uv", "v_mean_uv")):
                    line.set_data(times, [r[key] for r in self.history])
                    ax.relim()
                    ax.autoscale_view()
                self.axes[-1].set_xlim(max(0, times[-1] - 10), max(10, times[-1] + 0.1))
            self.fig.suptitle(f"{result['state']} | {result['candidate']} | "
                              f"dwell {result['dwell_sec']:.1f}s | {result['quality']}")
            self.fig.canvas.draw_idle()
            self.plot.pause(0.001)

    def close(self, status):
        self.handle.close()
        if self.plot is not None:
            self.plot.close(self.fig)
        write_json(self.path.with_suffix(".summary.json"), {
            "status": status, "rows": self.rows, "state_counts": dict(self.counts),
            "activation_counts": dict(self.activations), "source": self.source,
            "calibration_created_utc": self.model.get("created_utc"),
            "note": "Activation counts are detections, not accuracy measurements.",
        })


def run_playback(recording, model, sink, speed=1.0):
    speed = finite_number(speed, "Playback speed")
    if speed < 0:
        raise ValueError("Speed cannot be negative; zero means unpaced playback.")
    config = ProcessingConfig(**model["processing"])
    if recording.duration < config.warmup_sec + config.window_sec:
        raise ValueError(f"Recording is only {recording.duration:.3f}s; "
                         f"{config.warmup_sec + config.window_sec:.3f}s is required "
                         "for the first valid feature.")
    classifier = DwellClassifier(model)
    wall_start = time.monotonic()
    for feature in analyze_recording(recording, config):
        if speed:
            deadline = wall_start + feature.time_sec / speed
            while deadline > time.monotonic():
                time.sleep(min(0.05, deadline - time.monotonic()))
        sink.emit(classifier.update(feature))


def run_live(source, model, sink, duration=None, idle_timeout=10.0, max_latency=0.5):
    config = ProcessingConfig(**model["processing"])
    stream = FeatureStream(source.sfreq, config)
    classifier = DwellClassifier(model)
    if duration is not None and finite_number(duration, "Duration") <= 0:
        raise ValueError("Duration must be positive.")
    if not 0 < finite_number(max_latency, "Maximum latency") < finite_number(
            idle_timeout, "Idle timeout"):
        raise ValueError("Require 0 < max-latency < idle-timeout.")
    started = last_received = time.monotonic()
    origin = None
    disconnected = False
    while duration is None or time.monotonic() - started < duration:
        chunk = source.pull()
        now = time.monotonic()
        if chunk is None:
            if now - last_received > max_latency and not disconnected:
                stream.reset()
                classifier.reset()
                if origin is not None:
                    sink.emit(classifier.update(Feature(
                        source.clock() - origin, stream.generation, "GAP")))
                disconnected = True
            if now - last_received > idle_timeout:
                raise RuntimeError("EEG stream timed out; no fresh samples received.")
            continue
        data, timestamps = chunk
        age = source.clock() - timestamps[-1]
        if age < -0.1:
            raise ValueError("EEG timestamps are ahead of the local clock; check synchronization.")
        if age > max_latency:
            if not disconnected:
                stream.reset()
                classifier.reset()
                if origin is not None:
                    sink.emit(classifier.update(Feature(
                        source.clock() - origin, stream.generation, "STALE")))
                disconnected = True
            if now - last_received > idle_timeout:
                raise RuntimeError("Only stale EEG samples received; check stream buffering.")
            continue
        # A delayed network packet cannot bridge an elapsed wall-clock dropout.
        if now - last_received > max_latency and not disconnected:
            stream.reset()
            classifier.reset()
        last_received = now
        disconnected = False
        if origin is None:
            origin = timestamps[0]
        for feature in stream.push(data, timestamps - origin):
            sink.emit(classifier.update(feature))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    for name in ("playback", "live"):
        item = sub.add_parser(name)
        item.add_argument("--calibration", required=True)
        item.add_argument("--reference", required=True,
                          help="Actual acquisition reference; must match calibration")
        item.add_argument("--channel-map", help="Optional JSON canonical-to-input labels")
        item.add_argument("--output", help="New CSV path; existing files are never overwritten")
        item.add_argument("--plot", action="store_true")
        if name == "playback":
            item.add_argument("recording")
            item.add_argument("--speed", type=float, default=1.0,
                              help="Playback multiplier; 0 processes without waiting")
        else:
            selector = item.add_mutually_exclusive_group(required=True)
            selector.add_argument("--stream-name")
            selector.add_argument("--source-id")
            item.add_argument("--units", choices=("V", "mV", "uV"),
                              help="Override stream units after verifying acquisition scaling")
            item.add_argument("--duration", type=float)
            item.add_argument("--idle-timeout", type=float, default=10)
            item.add_argument("--max-latency", type=float, default=0.5)
    args = parser.parse_args(argv)
    source = sink = None
    status = "failed"
    try:
        model = calibration_model(read_json(args.calibration))
        mapping = read_json(args.channel_map) if args.channel_map else model.get("channel_map")
        if args.mode == "playback":
            recording = load_recording(args.recording, mapping)
            check_compatibility(model, recording.sfreq, args.reference)
            config = ProcessingConfig(**model["processing"])
            if recording.duration < config.warmup_sec + config.window_sec:
                raise ValueError(f"Recording is only {recording.duration:.3f}s; "
                                 "too short for processing warm-up and a full feature window.")
            metadata = {"mode": "playback", **recording.metadata}
        else:
            from lsl_input import LSLSource
            source = LSLSource(args.stream_name, args.source_id, mapping, args.units)
            check_compatibility(model, source.sfreq, args.reference)
            metadata = source.metadata
        metadata["reference"] = args.reference
        output = args.output or datetime.now().strftime(
            f"output/{args.mode}_%Y%m%d_%H%M%S_%f.csv")
        sink = ResultSink(output, model, metadata, args.plot)
        if args.mode == "playback":
            run_playback(recording, model, sink, args.speed)
        else:
            run_live(source, model, sink, args.duration, args.idle_timeout, args.max_latency)
        status = "complete"
        return 0
    except KeyboardInterrupt:
        status = "stopped"
        print("\nClassification stopped.")
        return 0
    except (ValueError, KeyError, TypeError, OSError, ImportError, RuntimeError) as exc:
        parser.exit(2, f"Classification failed: {exc}\n")
    finally:
        if source is not None:
            source.close()
        if sink is not None:
            sink.close(status)


if __name__ == "__main__":
    main()
