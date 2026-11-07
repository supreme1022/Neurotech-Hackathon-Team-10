"""Calibration protocol construction and explicit EEG/session alignment."""
from __future__ import annotations

import uuid

import numpy as np

from eog_pipeline import LABELS, finite_number


def build_protocol(repetitions=3, hold_sec=10.0, center_sec=6.0,
                   blink_sec=6.0, warmup_sec=8.0):
    if not isinstance(repetitions, int) or repetitions < 2:
        raise ValueError("At least two repetitions are required for held-out validation.")
    for name, value in (("hold", hold_sec), ("center", center_sec),
                        ("blink", blink_sec), ("warmup", warmup_sec)):
        if finite_number(value, name) < 5:
            raise ValueError(f"{name} duration must be at least five seconds.")
    protocol = [{"label": "CENTER", "repeat": -1, "duration_sec": warmup_sec}]
    # Rotate the first direction between repeats to reduce a fixed order effect.
    directions = ["RIGHT", "LEFT", "UP", "DOWN"]
    for repeat in range(repetitions):
        order = directions[repeat % 4:] + directions[:repeat % 4]
        for label in order:
            protocol.append({"label": "CENTER", "repeat": repeat,
                             "duration_sec": center_sec})
            protocol.append({"label": label, "repeat": repeat,
                             "duration_sec": hold_sec})
        protocol.append({"label": "CENTER", "repeat": repeat,
                         "duration_sec": center_sec})
        protocol.append({"label": "BLINK", "repeat": repeat,
                         "duration_sec": blink_sec})
    protocol.append({"label": "CENTER", "repeat": repetitions - 1,
                     "duration_sec": center_sec})
    return protocol


def new_session(protocol, geometry, marker_mode):
    return {
        "schema_version": 1, "session_id": uuid.uuid4().hex,
        "status": "ready", "protocol": protocol, "events": [],
        "screen": geometry, "marker_mode": marker_mode,
        "clock": "perf_counter; relative to first displayed target",
        "recording_control": "external; recording status is not verified by GUI",
    }


def marker_name(session_id, trial_id, label):
    return f"EOG|{session_id}|{trial_id}|{label}"


def align_trials(session, recording, offset_sec=None, settle_sec=2.0, trim_end_sec=0.25):
    """Return labeled recording intervals; never infer alignment from wall time."""
    if session.get("schema_version") != 1 or session.get("status") != "complete":
        raise ValueError("Session must use schema 1 and have status 'complete'.")
    events = session.get("events", [])
    if not events or not session.get("end_marker"):
        raise ValueError("Session has no complete target log/end marker.")
    if finite_number(settle_sec, "settle_sec") < 0 or finite_number(
            trim_end_sec, "trim_end_sec") < 0:
        raise ValueError("Settling and end trim cannot be negative.")
    previous_end = -np.inf
    trial_ids = set()
    for event in events:
        onset = finite_number(event["onset_sec"], "Target onset")
        duration = finite_number(event["duration_sec"], "Target duration")
        if onset < 0 or duration <= 0 or onset < previous_end - 1e-6:
            raise ValueError("Target times must be positive-duration and nonoverlapping.")
        previous_end = onset + duration
        if event["label"] not in LABELS or not isinstance(event["repeat"], int):
            raise ValueError("Unknown target label or invalid repetition.")
        if event["trial_id"] in trial_ids:
            raise ValueError("Target trial IDs must be unique.")
        trial_ids.add(event["trial_id"])

    if offset_sec is None:
        needed = [e["marker"] for e in events] + [session["end_marker"]]
        observed = {}
        for annotation in recording.annotations:
            name = annotation["description"]
            if name in needed:
                observed.setdefault(name, []).append(annotation["onset_sec"])
        missing = [name for name in needed if len(observed.get(name, [])) != 1]
        if missing:
            raise ValueError(
                "Cannot align session: target markers are missing or duplicated in EEG. "
                "LSL markers are not automatically embedded in CNT. Supply --offset "
                "only after independently measuring the recording time of the first "
                "target, or configure acquisition to retain the exact markers."
            )
        boundaries = [observed[name][0] for name in needed]
        if np.any(np.diff(boundaries) <= 0):
            raise ValueError("EEG target markers are not in protocol order.")
        expected = [e["duration_sec"] for e in events]
        if np.any(np.abs(np.diff(boundaries) - expected) > 0.25):
            raise ValueError("EEG markers disagree with session durations by >250 ms.")
        alignment = {"method": "acquisition_markers", "offset_sec": boundaries[0]}
    else:
        offset_sec = finite_number(offset_sec, "Recording offset")
        boundaries = [e["onset_sec"] + offset_sec for e in events]
        boundaries.append(events[-1]["onset_sec"] + events[-1]["duration_sec"] + offset_sec)
        alignment = {"method": "operator_verified_offset", "offset_sec": offset_sec}

    if boundaries[0] < -1 / recording.sfreq or boundaries[-1] > recording.duration + 1 / recording.sfreq:
        raise ValueError(
            f"Session spans {boundaries[0]:.3f}..{boundaries[-1]:.3f}s but recording "
            f"is only {recording.duration:.3f}s. Record the complete protocol."
        )
    trials = []
    for i, event in enumerate(events):
        start, end = boundaries[i], boundaries[i + 1]
        if event["repeat"] < 0:
            continue
        trials.append({
            "trial_id": event["trial_id"], "label": event["label"],
            "repeat": event["repeat"], "onset_sec": start, "end_sec": end,
            "usable_start_sec": start + settle_sec,
            "usable_end_sec": end - trim_end_sec,
        })
    return trials, alignment

