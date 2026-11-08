"""Reconstruct the calibration_GUI dot schedule from the EEG itself.

Use this when the GUI's session JSON is missing, or its recording offset was never
measured. The horizontal eye signal (F8 - F7) is matched against the dot schedule for
several hold lengths; the best match gives the hold length and the recording time of the
first target. It writes a session JSON (schema 1, marked "reconstructed") that
calibration.py accepts together with the printed --offset.

    python estimate_offset.py recording.cnt --output output/session_reconstructed.json

Check the printed match quality and the plot before trusting it. If the real GUI session
file turns up, prefer it: it has the measured onsets, this one has the nominal ones.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from scipy.signal import butter, sosfiltfilt

from calibration_session import build_protocol, marker_name
from eog_pipeline import load_recording, write_json

RATE = 50  # Hz used for the matching; glances are far slower than this


def horizontal_eog(recording):
    sos = butter(4, 5.0, btype="low", fs=recording.sfreq, output="sos")
    data = sosfiltfilt(sos, np.nan_to_num(recording.data) * 1e6, axis=1)
    step = max(1, int(round(recording.sfreq / RATE)))
    h = (data[1] - data[0])[::step]
    h = h - np.median(h)
    return np.clip(h, -400, 400), recording.sfreq / step


def template(protocol, fs):
    values = {"RIGHT": 1.0, "LEFT": -1.0}
    parts = [np.full(int(round(p["duration_sec"] * fs)), values.get(p["label"], 0.0))
             for p in protocol]
    return np.concatenate(parts)


def scan(signal, pattern, offsets):
    n, total = len(pattern), len(signal)
    for off in offsets:
        a, b = max(0, off), min(total, off + n)
        if b - a < 0.6 * n:
            continue
        segment, piece = signal[a:b], pattern[a - off:b - off]
        if piece.std() == 0 or segment.std() == 0:
            continue
        yield float(np.corrcoef(segment, piece)[0, 1]), off


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("recording", help="ANT CNT or EDF recording")
    parser.add_argument("--output", required=True, help="Session JSON to write")
    parser.add_argument("--holds", default="5,6,8,10,12,15",
                        help="Candidate hold lengths in seconds (GUI default 10)")
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--center", type=float, default=6)
    parser.add_argument("--blink", type=float, default=6)
    parser.add_argument("--warmup", type=float, default=8)
    parser.add_argument("--search", type=float, default=60,
                        help="Seconds before/after the recording start to search")
    parser.add_argument("--plot", help="Optional PNG of the match")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    output = Path(args.output)
    if output.exists() and not args.overwrite:
        parser.exit(2, f"{output} already exists; choose another path or use --overwrite.\n")

    recording = load_recording(args.recording)
    signal, fs = horizontal_eog(recording)
    best = None
    print(f"Recording: {recording.duration:.1f} s")
    for hold in (float(h) for h in args.holds.split(",")):
        protocol = build_protocol(args.repetitions, hold, args.center, args.blink, args.warmup)
        pattern = template(protocol, fs)
        coarse = list(scan(signal, pattern, range(-int(args.search * fs), int(args.search * fs) + 1, 5)))
        if not coarse:
            continue
        r, off = max(coarse, key=lambda x: abs(x[0]))
        fine = list(scan(signal, pattern, range(off - 2 * int(fs), off + 2 * int(fs) + 1)))
        r, off = max(fine, key=lambda x: abs(x[0]))
        runner_up = max((abs(x[0]) for x in coarse if abs(x[1] - off) > 3 * fs), default=0.0)
        print(f"  hold {hold:4.1f} s: protocol {len(pattern) / fs:5.0f} s, |r| = {abs(r):.3f} "
              f"at offset {off / fs:+.2f} s (next best elsewhere {runner_up:.3f})")
        if best is None or abs(r) > abs(best["r"]):
            best = {"hold_sec": hold, "r": r, "offset_sec": off / fs, "runner_up": runner_up,
                    "protocol": protocol}
    if best is None:
        parser.exit(2, "No protocol fits inside this recording.\n")

    offset, r = best["offset_sec"], best["r"]
    print(f"\nBest match: hold {best['hold_sec']:g} s, first target at {offset:.2f} s, r = {r:+.3f}")
    print("Polarity: F8-F7 positive = RIGHT" if r > 0 else
          "Polarity: F8-F7 positive = LEFT (calibration will learn this; just noting it)")
    if abs(r) < 0.4 or abs(r) - best["runner_up"] < 0.05:
        print("WARNING: weak or ambiguous match. Look at the plot before using this offset.")

    session_id = "reconstructed-" + Path(args.recording).stem[:24]
    events, t = [], 0.0
    for i, p in enumerate(best["protocol"]):
        events.append({"trial_id": str(i), "label": p["label"], "repeat": p["repeat"],
                       "onset_sec": t, "duration_sec": p["duration_sec"],
                       "marker": marker_name(session_id, str(i), p["label"]),
                       "lsl_timestamp": None})
        t += p["duration_sec"]
    write_json(output, {
        "schema_version": 1, "session_id": session_id, "status": "complete",
        "events": events, "end_marker": marker_name(session_id, "END", "END"),
        "duration_sec": t, "screen": None, "marker_mode": "none",
        "clock": "reconstructed: nominal protocol durations, not measured GUI onsets",
        "recording_control": "external", "reconstructed": True,
        "alignment_estimate": {"offset_sec": round(offset, 2), "r": round(r, 3),
                               "hold_sec": best["hold_sec"], "method": "template match on F8-F7"},
        "note": "Built by estimate_offset.py because the GUI session JSON was unavailable.",
    })
    print(f"Session written: {output}")
    print("\nNext:\n  python calibration.py "
          f"\"{args.recording}\" --session {output} --reference CPz --offset {offset:.2f} "
          "--directions RIGHT,LEFT --baseline-track 2 --baseline-rescue 15 --skip-repeats 1 "
          "--output output/calibration.json")

    if args.plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        pattern = template(best["protocol"], fs)
        shown = np.full(len(signal), np.nan)
        off = int(round(offset * fs))
        a, b = max(0, off), min(len(signal), off + len(pattern))
        shown[a:b] = pattern[a - off:b - off] * 200 * np.sign(r)
        times = np.arange(len(signal)) / fs
        fig, ax = plt.subplots(figsize=(16, 4))
        ax.plot(times, signal, lw=0.6, label="F8 - F7, low-pass 5 Hz (uV, clipped)")
        ax.plot(times, shown, lw=1.2, label=f"dot schedule (hold {best['hold_sec']:g} s, offset {offset:.2f} s)")
        ax.set_xlabel("seconds"); ax.set_ylabel("uV"); ax.legend(loc="upper right")
        ax.set_title(f"Protocol match r = {r:+.3f}")
        fig.tight_layout(); fig.savefig(args.plot, dpi=90)
        print(f"Plot written: {args.plot}")
    return 0


if __name__ == "__main__":
    main()
