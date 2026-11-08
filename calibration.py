"""Fit and validate a subject/session-specific calibration from labeled ANT CNT/EDF."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
import csv
import json

import numpy as np

from calibration_session import align_trials
from eog_pipeline import (
    CHANNELS, DIRECTIONS, LABELS, PROCESSING_VERSION, SCHEMA_VERSION,
    ProcessingConfig, analyze_recording, calibration_model, candidate_for,
    finite_number, load_recording, model_axes, read_json, write_json,
)


def center_spans_for(trials, alignment=None):
    """Recording intervals where the target was CENTER, including the initial warm-up."""
    spans = [(t["onset_sec"], t["end_sec"]) for t in trials if t["label"] == "CENTER"]
    if alignment is not None and trials:
        spans.append((alignment["offset_sec"], min(t["onset_sec"] for t in trials)))
    return spans


def centered_mean(feature, baseline_uv):
    base = feature.baseline_uv if feature.baseline_uv is not None else baseline_uv
    return np.asarray(feature.mean_uv, dtype=float) - np.asarray(base, dtype=float)


def labeled_features(recording, config, trials, center_spans=None):
    """OK windows inside usable targets. With drift tracking enabled, each window also
    carries the label-guided baseline: it follows the signal only while the target is
    CENTER (same time constant as the live classifier, which uses its own CENTER calls)."""
    tracking = config.baseline_track_sec is not None
    alpha = min(1.0, config.step_sec / config.baseline_track_sec) if tracking else 0.0
    spans = center_spans if center_spans is not None else center_spans_for(trials)
    baseline = None
    rows = []
    for feature in analyze_recording(recording, config):
        if feature.quality != "OK":
            continue
        if tracking:
            mean = np.asarray(feature.mean_uv, dtype=float)
            end = feature.time_sec + 1 / recording.sfreq
            in_center = any(feature.window_start_sec >= a - 1e-9 and end <= b + 1e-9
                            for a, b in spans)
            if baseline is None and in_center:
                baseline = mean.copy()
            feature.baseline_uv = None if baseline is None else baseline.tolist()
            if in_center:
                baseline = baseline + alpha * (mean - baseline)
        for trial in trials:
            # Every sample of the feature window must be within a usable target.
            if (feature.window_start_sec >= trial["usable_start_sec"] - 1e-9 and
                    feature.time_sec + 1 / recording.sfreq <= trial["usable_end_sec"] + 1e-9):
                if not tracking or feature.baseline_uv is not None:
                    rows.append((feature, trial))
                break
    return rows


def fit_parameters(rows, config, directions=DIRECTIONS):
    baseline = np.median([f.mean_uv for f, t in rows if t["label"] == "CENTER"], axis=0)
    stable = [(f, t) for f, t in rows if t["label"] != "BLINK"]
    variances = np.asarray([f.variance_uv2 for f, _ in stable])
    variance_limits = np.maximum(1.0, np.quantile(variances, 0.99, axis=0) * 1.5)
    rules = {}
    for label in directions:
        axis = 0 if label in ("RIGHT", "LEFT") else 1
        positive = np.asarray([centered_mean(f, baseline)[axis]
                               for f, t in stable if t["label"] == label])
        negative = np.asarray([centered_mean(f, baseline)[axis]
                               for f, t in stable if t["label"] != label])
        polarity = 1 if np.median(positive) > 0 else -1
        positive_low = float(np.quantile(positive * polarity, 0.1))
        negative_high = max(0.0, float(np.quantile(negative * polarity, 0.95)))
        if positive_low - negative_high < 1.0:
            raise ValueError(
                f"{label} is not separable from other targets with the current virtual "
                "EOG axes (less than 1 uV margin). Check labels, reference, artifacts, "
                "or collect dedicated EOG channels."
            )
        rules[label] = {
            "axis": axis, "polarity": polarity,
            "threshold_uv": (positive_low + negative_high) / 2,
            "training_margin_uv": positive_low - negative_high,
        }
    for a, b in (("RIGHT", "LEFT"), ("UP", "DOWN")):
        if a in rules and b in rules and rules[a]["polarity"] == rules[b]["polarity"]:
            raise ValueError(f"{a}/{b} do not have opposite polarity. Check labeled data.")
    return baseline.tolist(), variance_limits.tolist(), rules


def validation_report(rows, model, minimum_accuracy):
    fitted = set(model["directions"])
    scores_blink = 1 in model_axes(model)  # only a vertical model can tell blinks apart

    def truth_of(label):
        # A target this model does not detect must read as neutral, never as a command.
        if label in fitted or label == "CENTER" or (label == "BLINK" and scores_blink):
            return label
        return "CENTER"

    labels = [label for label in LABELS if truth_of(label) == label]
    confusion = {label: {} for label in labels}
    trials = {}
    for feature, trial in rows:
        prediction = candidate_for(feature, model, baseline=feature.baseline_uv)
        if prediction == "TRANSITION_BLINK":
            prediction = "BLINK" if scores_blink else "CENTER"
        truth = truth_of(trial["label"])
        counts = confusion[truth]
        counts[prediction] = counts.get(prediction, 0) + 1
        item = trials.setdefault(trial["trial_id"], {"truth": truth, "predictions": []})
        item["predictions"].append(prediction)
    per_class = {}
    for label, counts in confusion.items():
        count = sum(counts.values())
        per_class[label] = {"windows": count,
                            "recall": counts.get(label, 0) / count if count else 0.0}
    correct_trials = 0
    for item in trials.values():
        predictions = item.pop("predictions")
        item["prediction"] = max(set(predictions), key=lambda p: (predictions.count(p), p))
        item["correct"] = item["prediction"] == item["truth"]
        correct_trials += item["correct"]
    trial_accuracy = correct_trials / len(trials) if trials else 0.0
    passed = (all(item["recall"] >= minimum_accuracy for item in per_class.values())
              and trial_accuracy >= minimum_accuracy)
    return {
        "passed": passed, "minimum_required_recall": minimum_accuracy,
        "per_class": per_class, "confusion": confusion,
        "held_out_trial_accuracy": trial_accuracy, "trials": trials,
        "neutral_false_direction_rate": (
            sum(count for label, count in confusion["CENTER"].items() if label in DIRECTIONS)
            / max(1, sum(confusion["CENTER"].values()))
        ),
        "note": "Overlapping windows are correlated. Entire final repetition is held out; "
                "these metrics are not an independent clinical or deployment validation.",
    }



def behavior_report(recording, config, model, trials, held_out_repeat, minimum_accuracy):
    """Evaluate actual dwell activations on the untouched final repetition."""
    from eog_pipeline import DwellClassifier

    classifier = DwellClassifier({**model, "quality": {"passed": True}})
    validation_trials = [t for t in trials if t["repeat"] == held_out_repeat]
    detections = {t["trial_id"]: [] for t in validation_trials}
    errors = []
    for feature in analyze_recording(recording, config):
        result = classifier.update(feature)
        if not result["activated"]:
            continue
        trial = next((t for t in validation_trials
                      if t["onset_sec"] <= feature.time_sec < t["end_sec"]), None)
        if trial is None:
            continue
        detection = {
            "time_sec": feature.time_sec, "direction": result["state"],
            "latency_sec": feature.time_sec - trial["onset_sec"],
        }
        detections[trial["trial_id"]].append(detection)
        if result["state"] != trial["label"]:
            errors.append({"trial_id": trial["trial_id"], "expected": trial["label"],
                           **detection})
    directional_trials = [t for t in validation_trials if t["label"] in model["directions"]]
    successes = 0
    latencies = []
    for trial in directional_trials:
        correct = [d for d in detections[trial["trial_id"]]
                   if d["direction"] == trial["label"]]
        if correct:
            successes += 1
            latencies.append(correct[0]["latency_sec"])
    recall = successes / len(directional_trials) if directional_trials else 0.0
    return {
        "passed": recall >= minimum_accuracy and not errors,
        "directional_trial_recall": recall,
        "false_activation_count": len(errors), "false_activations": errors,
        "first_activation_latency_sec": latencies,
        "mean_first_activation_latency_sec": float(np.mean(latencies)) if latencies else None,
        "detections_by_trial": detections,
        "acceptance": "Required directional-trial recall and zero wrong/neutral/blink "
                      "activations on the held-out repetition.",
    }


def calibrate(recording, session, reference, config=None, offset_sec=None,
              settle_sec=2.0, trim_end_sec=0.25, minimum_accuracy=0.8,
              directions=DIRECTIONS, skip_repeats=0):
    config = (config or ProcessingConfig()).validate(recording.sfreq)
    if not reference.strip():
        raise ValueError("Supply the acquisition reference, e.g. CPz.")
    directions = tuple(directions)
    if not directions or set(directions) - set(DIRECTIONS):
        raise ValueError(f"Directions must be a non-empty subset of {DIRECTIONS}.")
    if isinstance(skip_repeats, bool) or not isinstance(skip_repeats, int) or skip_repeats < 0:
        raise ValueError("skip_repeats must be a non-negative integer.")
    minimum_accuracy = finite_number(minimum_accuracy, "Minimum accuracy")
    if not 0.5 <= minimum_accuracy <= 1:
        raise ValueError("Minimum accuracy must be between 0.5 and 1.")
    if recording.duration < config.warmup_sec + config.window_sec:
        raise ValueError(f"Recording is only {recording.duration:.3f}s; at least "
                         f"{config.warmup_sec + config.window_sec:.3f}s is needed even "
                         "for one feature. Record the complete labeled protocol.")
    all_trials, alignment = align_trials(session, recording, offset_sec, settle_sec, trim_end_sec)
    # Fresh gel electrodes drift fast for the first minute or so; the first repetition(s)
    # can be treated as settling time and left out of fitting and validation. The drift
    # tracker still runs through them, exactly as it would live.
    trials = [t for t in all_trials if t["repeat"] >= skip_repeats]
    repeats = sorted({t["repeat"] for t in trials})
    if len(repeats) < 2:
        raise ValueError("At least two complete repetitions are required"
                         + (f" after skipping {skip_repeats}." if skip_repeats else "."))
    # Split before parameter fitting; no overlapping window can cross a trial.
    held_out_repeat = repeats[-1]
    rows = labeled_features(recording, config, trials, center_spans_for(all_trials, alignment))
    for repeat in repeats:
        for label in LABELS:
            count = sum(t["repeat"] == repeat and t["label"] == label for _, t in rows)
            if count < 3:
                raise ValueError(f"Repeat {repeat + 1} / {label} has only {count} usable "
                                 "windows. Extend holds, reduce missing data, or recollect.")
    train = [(f, t) for f, t in rows if t["repeat"] != held_out_repeat]
    test = [(f, t) for f, t in rows if t["repeat"] == held_out_repeat]
    baseline, variance_limits, rules = fit_parameters(train, config, directions)
    model = {
        "schema_version": SCHEMA_VERSION, "processing_version": PROCESSING_VERSION,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "units": {"amplitude": "uV", "variance": "uV^2"},
        "sfreq_hz": recording.sfreq, "reference": reference.strip(),
        "reference_verification": "operator supplied; confirm acquisition settings",
        "processing": asdict(config), "baseline_uv": baseline,
        "variance_limits_uv2": variance_limits, "directions": rules,
        "channel_map": recording.metadata["channels"],
        "axes": {"horizontal": "F8 - F7", "vertical": "(Fp1 + Fp2) / 2"},
        "source": recording.metadata,
        "session": {"session_id": session["session_id"], "screen": session.get("screen"),
                    "alignment": alignment, "held_out_repeat": held_out_repeat,
                    "skipped_repeats": skip_repeats,
                    "settle_sec": settle_sec, "trim_end_sec": trim_end_sec},
    }
    quality = validation_report(test, model, minimum_accuracy)
    quality["behavior"] = behavior_report(recording, config, model, trials,
                                           held_out_repeat, minimum_accuracy)
    quality["passed"] = quality["passed"] and quality["behavior"]["passed"]
    model["quality"] = quality
    if quality["passed"]:
        calibration_model(model)
    return model, rows, trials


def save_features(path, rows, held_out_repeat):
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["time_sec", "trial_id", "repeat", "label", "split",
                         "h_mean_uv", "v_mean_uv", "h_variance_uv2", "v_variance_uv2",
                         "h_baseline_uv", "v_baseline_uv"])
        for feature, trial in rows:
            writer.writerow([feature.time_sec, trial["trial_id"], trial["repeat"],
                             trial["label"],
                             "validation" if trial["repeat"] == held_out_repeat else "training",
                             *feature.mean_uv, *feature.variance_uv2,
                             *(feature.baseline_uv or ["", ""])])


def save_diagnostics(path, rows, trials, model):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
    times = [f.time_sec for f, _ in rows]
    means = np.asarray([centered_mean(f, model["baseline_uv"]) for f, _ in rows])
    variances = np.asarray([f.variance_uv2 for f, _ in rows])
    for axis, name in enumerate(("Horizontal", "Vertical")):
        axes[0].plot(times, means[:, axis], ".", ms=2, label=name)
        axes[1].plot(times, variances[:, axis], ".", ms=2, label=name)
        axes[1].axhline(model["variance_limits_uv2"][axis], linestyle="--", alpha=0.6)
    for label, rule in model["directions"].items():
        axes[0].axhline(rule["threshold_uv"] * rule["polarity"], linestyle="--",
                        alpha=0.5, label=label)
    for trial in trials:
        for ax in axes:
            ax.axvspan(trial["onset_sec"], trial["end_sec"], alpha=0.04,
                       color="red" if trial["label"] == "BLINK" else "blue")
        axes[0].text((trial["onset_sec"] + trial["end_sec"]) / 2, 1.01, trial["label"],
                     rotation=90, ha="center", va="bottom",
                     transform=axes[0].get_xaxis_transform(), fontsize=6)
    axes[0].set_ylabel("Centered mean (uV)")
    axes[1].set_ylabel("Variance (uV^2)")
    axes[1].set_yscale("symlog", linthresh=1)
    axes[1].set_xlabel("Time in recording (seconds)")
    for ax in axes:
        ax.legend(loc="upper right")
        ax.grid(alpha=0.2)
    fig.suptitle("Calibration diagnostics — " + ("PASSED" if model["quality"]["passed"] else "FAILED"))
    fig.tight_layout(rect=[0, 0, 1, 0.9])
    fig.savefig(path)
    plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("recording", help="ANT CNT or EDF recording")
    parser.add_argument("--session", required=True, help="Completed GUI session JSON")
    parser.add_argument("--reference", required=True, help="Reference used during acquisition")
    parser.add_argument("--output", default="output/calibration.json")
    parser.add_argument("--offset", type=float, help="Verified EEG time of FIRST target, seconds")
    parser.add_argument("--channel-map", help='JSON file mapping canonical names to recording labels')
    parser.add_argument("--settle", type=float, default=2.0)
    parser.add_argument("--trim-end", type=float, default=0.25)
    parser.add_argument("--lowpass", type=float, default=5.0)
    parser.add_argument("--highpass", type=float, default=None,
                        help="Optional cutoff; default preserves DC (low-pass only)")
    parser.add_argument("--warmup", type=float, default=2.0)
    parser.add_argument("--minimum-accuracy", type=float, default=0.8)
    parser.add_argument("--directions", default=",".join(DIRECTIONS),
                        help="Comma-separated subset to calibrate, e.g. RIGHT,LEFT for a "
                             "horizontal-only model (other targets must then read as neutral)")
    parser.add_argument("--baseline-track", type=float, default=None,
                        help="Drift tracking time constant in seconds: the baseline follows "
                             "the signal while gaze is at CENTER. Default: fixed baseline")
    parser.add_argument("--baseline-rescue", type=float, default=None,
                        help="With tracking: a direction held longer than this many seconds "
                             "is treated as drift and the baseline re-centres")
    parser.add_argument("--skip-repeats", type=int, default=0,
                        help="Leave the first N repetitions out of fitting and validation "
                             "(electrode settling). At least two must remain.")
    parser.add_argument("--no-plot", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    output = Path(args.output)
    try:
        if output.exists() and not args.overwrite:
            raise ValueError(f"{output} already exists; choose another path or use --overwrite.")
        mapping = read_json(args.channel_map) if args.channel_map else None
        recording = load_recording(args.recording, mapping)
        session = read_json(args.session)
        config = ProcessingConfig(lowpass_hz=args.lowpass, highpass_hz=args.highpass,
                                  warmup_sec=args.warmup,
                                  baseline_track_sec=args.baseline_track,
                                  baseline_rescue_sec=args.baseline_rescue)
        directions = tuple(d.strip().upper() for d in args.directions.split(",") if d.strip())
        model, rows, trials = calibrate(
            recording, session, args.reference, config, args.offset,
            args.settle, args.trim_end, args.minimum_accuracy, directions,
            args.skip_repeats)
        output.parent.mkdir(parents=True, exist_ok=True)
        write_json(output.with_suffix(".report.json"), model)
        save_features(output.with_suffix(".features.csv"), rows,
                      model["session"]["held_out_repeat"])
        if not args.no_plot:
            save_diagnostics(output.with_suffix(".diagnostics.png"), rows, trials, model)
        if not model["quality"]["passed"]:
            raise ValueError("Held-out quality checks failed. Inspect report/diagnostics. "
                             "No usable calibration was written; any existing calibration "
                             "was left unchanged.")
        write_json(output, model)
        print(f"Calibration saved: {output}")
        print(json.dumps(model["quality"]["per_class"], indent=2))
        return 0
    except (ValueError, KeyError, TypeError, OSError, ImportError, RuntimeError) as exc:
        parser.exit(2, f"Calibration failed: {exc}\n")


if __name__ == "__main__":
    main()
