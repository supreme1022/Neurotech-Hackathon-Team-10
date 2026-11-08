"""Print EEG direction commands while replaying a saved CNT/EDF recording.

Default: recording.cnt + output/recovered/calibration.json, paced at 1x speed.
The recovered model preprocesses the entire file before the playback clock starts;
it is recorded playback, not inference from a live EEG amplifier.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout
from dataclasses import dataclass
import json
from pathlib import Path
import sys
import time
from typing import Callable, Iterable

from eog_pipeline import (
    DIRECTIONS, DwellClassifier, ProcessingConfig, analyze_recording,
    calibration_model, check_compatibility, finite_number, load_recording, read_json,
)


@dataclass(frozen=True)
class DirectionEvent:
    sequence: int
    time_sec: float
    direction: str
    mode: str

    def as_dict(self):
        """Stable event format for a future backend/frontend transport."""
        return {"type": "direction", "sequence": self.sequence,
                "time_sec": round(self.time_sec, 3),
                "direction": self.direction, "mode": self.mode}


def prepare_directions(recording, model, *, mode="commands", interval_sec=1.0):
    """Infer solely from EEG and saved parameters; no GUI target log is read.

    commands: one event per dwell activation. labels: eligible direction changes
    and periodic direction labels, before dwell confirmation. Invalid/neutral
    sections never produce a direction in either mode.
    """
    if mode not in ("commands", "labels"):
        raise ValueError("Mode must be 'commands' or 'labels'.")
    interval_sec = finite_number(interval_sec, "Label interval")
    if interval_sec <= 0:
        raise ValueError("Label interval must be positive.")
    config = ProcessingConfig(**model["processing"])
    config.validate(recording.sfreq)
    if recording.duration < config.warmup_sec + config.window_sec:
        raise ValueError("Recording is too short for warm-up and a complete feature window.")
    classifier = DwellClassifier(model)
    events = []
    previous = None
    previous_time = None
    for feature in analyze_recording(recording, config):
        result = classifier.update(feature)
        if mode == "commands":
            if not result["activated"] or result["state"] not in DIRECTIONS:
                continue
            direction = result["state"]
        else:
            # During a paused blink, candidate may retain the previous direction.
            # Only eligible states may reach the output, never that retained label.
            if (result["state"] not in (*DIRECTIONS, "DWELLING") or
                    result["candidate"] not in DIRECTIONS or result["quality"] != "OK"):
                previous = previous_time = None
                continue
            direction = result["candidate"]
            if (direction == previous and previous_time is not None and
                    feature.time_sec - previous_time < interval_sec - 1e-9):
                continue
            previous, previous_time = direction, feature.time_sec
        events.append(DirectionEvent(len(events) + 1, float(feature.time_sec),
                                     direction.lower(), mode))
    return events


def replay_directions(events: Iterable[DirectionEvent], duration_sec: float,
                      on_direction: Callable[[DirectionEvent], None], *, speed=1.0,
                      clock=time.monotonic, sleep=time.sleep):
    """Deliver events at absolute source-time deadlines, with no cumulative delay.

    A future UI bridge can replace on_direction without changing classification.
    No networking or frontend is started by this script.
    """
    speed = finite_number(speed, "Playback speed")
    duration_sec = finite_number(duration_sec, "Recording duration")
    if speed < 0 or duration_sec < 0:
        raise ValueError("Speed and recording duration cannot be negative.")
    events = list(events)
    previous_time = -1.0
    for event in events:
        timestamp = finite_number(event.time_sec, "Event time")
        if timestamp < 0 or timestamp < previous_time or timestamp > duration_sec:
            raise ValueError("Direction events must be ordered and within the recording.")
        if event.direction not in {name.lower() for name in DIRECTIONS}:
            raise ValueError("Unknown direction event.")
        previous_time = timestamp
    started = clock()

    def wait_until(source_time):
        if speed == 0:
            return
        deadline = started + source_time / speed
        while True:
            remaining = deadline - clock()
            if remaining <= 0:
                return
            sleep(min(0.05, remaining))

    for event in events:
        wait_until(event.time_sec)
        on_direction(event)
    # Keep silent neutral sections at the end rather than ending playback early.
    wait_until(duration_sec)


def print_direction(event, *, json_output=False, timestamps=False, stream=None):
    stream = sys.stdout if stream is None else stream
    if json_output:
        line = json.dumps(event.as_dict(), separators=(",", ":"), allow_nan=False)
    elif timestamps:
        line = f"{event.time_sec:8.3f}s {event.direction}"
    else:
        line = event.direction
    print(line, file=stream, flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("recording", nargs="?", default="recording.cnt")
    parser.add_argument("--calibration", default="output/recovered/calibration.json")
    parser.add_argument("--reference", default="CPz", help="Actual acquisition reference")
    parser.add_argument("--mode", choices=("commands", "labels"), default="commands")
    parser.add_argument("--interval", type=float, default=1.0,
                        help="Record-time seconds between unchanged labels; default 1")
    parser.add_argument("--speed", type=float, default=1.0,
                        help="Playback multiplier; 1 is real time, 0 skips waiting")
    formatting = parser.add_mutually_exclusive_group()
    formatting.add_argument("--timestamps", action="store_true")
    formatting.add_argument("--json", action="store_true", help="One JSON event per stdout line")
    args = parser.parse_args(argv)
    try:
        speed = finite_number(args.speed, "Playback speed")
        if speed < 0:
            raise ValueError("Playback speed cannot be negative.")
        if not Path(args.calibration).is_file():
            raise ValueError(f"Calibration not found: {args.calibration}. "
                             "Create it first or select a file with --calibration.")
        print(f"Loading {args.recording} and preparing EEG classifications...", file=sys.stderr)
        # Library diagnostics must not contaminate the direction/JSON output.
        with redirect_stdout(sys.stderr):
            model = calibration_model(read_json(args.calibration))
            recording = load_recording(args.recording, model.get("channel_map"))
            check_compatibility(model, recording.sfreq, args.reference)
            events = prepare_directions(recording, model, mode=args.mode,
                                        interval_sec=args.interval)
        print(f"Playing {recording.duration:.1f}s | mode={args.mode} | speed={speed:g}x | "
              "Ctrl+C to stop. Directions go to stdout; these messages go to stderr.",
              file=sys.stderr)
        if model["processing"].get("offline_detrend_sec"):
            print("Using recorded-file preprocessing; this is not live EEG inference.",
                  file=sys.stderr)
        if args.mode == "labels" and model["quality"].get("acceptance_policy") == "command_trials":
            print("Labels are provisional; this model was accepted for held-gaze commands.",
                  file=sys.stderr)
        replay_directions(events, recording.duration,
                          lambda event: print_direction(event, json_output=args.json,
                                                        timestamps=args.timestamps),
                          speed=speed)
        print(f"Playback complete: {len(events)} direction events.", file=sys.stderr)
        return 0
    except KeyboardInterrupt:
        print("\nPlayback stopped.", file=sys.stderr)
        return 130
    except BrokenPipeError:
        return 0
    except (ValueError, KeyError, TypeError, OSError, ImportError, RuntimeError) as exc:
        parser.exit(2, f"Playback failed: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
