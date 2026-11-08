"""Fit and validate a subject/session-specific calibration from labeled ANT CNT/EDF."""
from __future__ import annotations

import argparse
from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path
import csv
import json

import numpy as np

from calibration_session import align_trials
from eog_pipeline import (
    CHANNELS, DIRECTIONS, LABELS, PROCESSING_VERSION, SCHEMA_VERSION,
    ProcessingConfig, analyze_recording, calibration_model, candidate_for,
    finite_number, load_recording, read_json, write_json, blink_residual,
)


def labeled_features(recording, config, trials):
    rows = []
    for feature in analyze_recording(recording, config):
        if feature.quality != "OK":
            continue
        for trial in trials:
            # Every sample of the feature window must be within a usable target.
            if (feature.window_start_sec >= trial["usable_start_sec"] - 1e-9 and
                    feature.time_sec + 1 / recording.sfreq <= trial["usable_end_sec"] + 1e-9):
                rows.append((feature, trial))
                break
    return rows


def fit_parameters(rows, config, minimum_accuracy=0.8):
    rows = [(f, t) for f, t in rows if not f.blink_recent]
    for label in ("CENTER", *DIRECTIONS):
        if not any(t["label"] == label for _, t in rows):
            raise ValueError(f"No blink-free training windows remain for {label}.")
    baseline = np.median([f.mean_uv for f, t in rows if t["label"] == "CENTER"], axis=0)
    stable = [(f, t) for f, t in rows if t["label"] != "BLINK"]
    variances = np.asarray([f.variance_uv2 for f, _ in stable])
    variance_limits = np.maximum(1.0, np.quantile(variances, 0.99, axis=0) * 1.5)
    rules = {}
    for label in DIRECTIONS:
        axis = 0 if label in ("RIGHT", "LEFT") else 1
        positive = np.asarray([f.mean_uv[axis] - baseline[axis]
                               for f, t in stable if t["label"] == label])
        negative = np.asarray([f.mean_uv[axis] - baseline[axis]
                               for f, t in stable if t["label"] != label
                               and not (config.hierarchical_axes and axis == 1
                                        and t["label"] in ("RIGHT", "LEFT"))])
        polarity = 1 if np.median(positive) > 0 else -1
        positive_low = float(np.quantile(positive * polarity, 0.1))
        negative_high = max(0.0, float(np.quantile(negative * polarity, 0.95)))
        threshold = (positive_low + negative_high) / 2
        training_min_recall = None
        if config.robust_features and config.hierarchical_axes:
            # Real class distributions can overlap. Select on training data,
            # then demand the same explicit recalls on held-out data, rather
            # than requiring a perfect quantile gap before validation runs.
            groups = [positive * polarity]
            for other in LABELS:
                if other in (label, "BLINK") or (axis == 1 and other in ("LEFT", "RIGHT")):
                    continue
                values = [(f.mean_uv[axis] - baseline[axis]) * polarity
                          for f, t in stable if t["label"] == other]
                if values:
                    groups.append(np.asarray(values))
            values = np.unique(np.r_[0.0, *groups])
            candidates = (values[:-1] + values[1:]) / 2
            best = None
            for candidate in candidates[candidates > 0]:
                recalls = [float(np.mean(groups[0] > candidate))] + [
                    float(np.mean(group <= candidate)) for group in groups[1:]]
                score = (min(recalls), float(np.mean(recalls)), float(candidate))
                if best is None or score > best:
                    best = score
            if best is None or best[0] < minimum_accuracy:
                raise ValueError(f"{label} is not separable at the required training recall "
                                 f"({best[0] if best else 0:.1%} vs {minimum_accuracy:.1%}).")
            training_min_recall, _, threshold = best
        elif positive_low - negative_high < 1.0:
            raise ValueError(
                f"{label} is not separable from other targets with the current virtual "
                f"EOG axes (margin {positive_low - negative_high:.2f} uV; need 1 uV). "
                "For a drifting recorded file, try --offline-drift. Check timing and "
                "inspect the signal before changing thresholds."
            )
        rules[label] = {
            "axis": axis, "polarity": polarity,
            "threshold_uv": threshold,
            "training_margin_uv": positive_low - negative_high,
            "training_min_recall": training_min_recall,
        }
    for a, b in (("RIGHT", "LEFT"), ("UP", "DOWN")):
        if rules[a]["polarity"] == rules[b]["polarity"]:
            raise ValueError(f"{a}/{b} do not have opposite polarity. Check labeled data.")
    return baseline.tolist(), variance_limits.tolist(), rules


def validation_report(rows, model, minimum_accuracy):
    confusion = {label: {} for label in LABELS}
    trials = {}
    excluded = {label: 0 for label in LABELS}
    for feature, trial in rows:
        truth = trial["label"]
        if model["processing"].get("blink_threshold_uv", 0):
            if truth == "BLINK":
                # A BLINK trial requests intermittent blinks, not closed eyes
                # during every frame. Evaluate presence within the full window.
                prediction = "BLINK" if feature.blink_fraction > 0 else "CENTER"
            elif feature.blink_recent:
                excluded[truth] += 1
                continue
            else:
                prediction = candidate_for(feature, model)
        else:
            prediction = candidate_for(feature, model)
        if prediction == "TRANSITION_BLINK":
            prediction = "BLINK"
        counts = confusion[truth]
        counts[prediction] = counts.get(prediction, 0) + 1
        item = trials.setdefault(trial["trial_id"], {"truth": truth, "predictions": []})
        item["predictions"].append(prediction)
    per_class = {}
    for label, counts in confusion.items():
        count = sum(counts.values())
        per_class[label] = {"windows": count,
                            "recall": counts.get(label, 0) / count if count else 0.0,
                            "excluded_current_blink_windows": excluded[label],
                            "eligible_fraction": count / (count + excluded[label])
                            if count + excluded[label] else 0.0}
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
                "these metrics are not an independent clinical or deployment validation. "
                "Offline blink-aware mode reports gaze recall on eligible windows and "
                "BLINK-trial detection coverage over full windows; these are different metrics.",
    }


def apply_acceptance(quality, policy="all_states"):
    """Keep strict window checks separate from explicit command-level acceptance."""
    if policy not in ("all_states", "command_trials"):
        raise ValueError("Unknown calibration acceptance policy.")
    quality["window_checks_passed"] = quality["passed"]
    quality["acceptance_policy"] = policy
    minimum = quality["minimum_required_recall"]
    behavior = quality["behavior"]
    commands_passed = (
        behavior["passed"] and behavior["false_activation_count"] == 0
        and quality["held_out_trial_accuracy"] >= minimum
        and quality["per_class"]["CENTER"]["recall"] >= minimum
        and quality["per_class"]["BLINK"]["recall"] >= minimum
        and all(item["windows"] > 0 for item in quality["per_class"].values()))
    quality["command_checks_passed"] = commands_passed
    quality["passed"] = (commands_passed if policy == "command_trials"
                         else quality["window_checks_passed"] and behavior["passed"])
    if policy == "command_trials":
        quality["acceptance_note"] = (
            "Accepted for recorded held-gaze commands, not continuous gaze accuracy. "
            "Requires directional command recall, majority-trial accuracy, neutral "
            "recall and blink coverage at the stated minimum, with zero false activations. "
            "Per-direction window recalls remain reported even when below the minimum.")
    return quality



def behavior_report(recording, config, model, trials, held_out_repeat, minimum_accuracy):
    """Evaluate actual dwell activations on the untouched final repetition."""
    from eog_pipeline import DwellClassifier

    classifier = DwellClassifier({**model, "quality": {"passed": True}})
    validation_trials = [t for t in trials
                         if held_out_repeat is None or t["repeat"] == held_out_repeat]
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
    directional_trials = [t for t in validation_trials if t["label"] in DIRECTIONS]
    successes = 0
    latencies = []
    duplicates = 0
    for trial in directional_trials:
        correct = [d for d in detections[trial["trial_id"]]
                   if d["direction"] == trial["label"]]
        if correct:
            successes += 1
            latencies.append(correct[0]["latency_sec"])
            duplicates += max(0, len(correct) - 1)
    recall = successes / len(directional_trials) if directional_trials else 0.0
    return {
        "passed": recall >= minimum_accuracy and not errors,
        "directional_trial_recall": recall,
        "false_activation_count": len(errors), "false_activations": errors,
        "duplicate_correct_activation_count": duplicates,
        "first_activation_latency_sec": latencies,
        "mean_first_activation_latency_sec": float(np.mean(latencies)) if latencies else None,
        "detections_by_trial": detections,
        "acceptance": "Required directional-trial recall and zero wrong/neutral/blink "
                      "activations on the held-out repetition.",
    }


def calibrate(recording, session, reference, config=None, offset_sec=None,
              settle_sec=2.0, trim_end_sec=0.25, minimum_accuracy=0.8,
              acceptance_policy="all_states"):
    config = (config or ProcessingConfig()).validate(recording.sfreq)
    if acceptance_policy == "command_trials" and not config.offline_detrend_sec:
        raise ValueError("Command-level acceptance requires the recorded-file profile.")
    if not reference.strip():
        raise ValueError("Supply the acquisition reference, e.g. CPz.")
    minimum_accuracy = finite_number(minimum_accuracy, "Minimum accuracy")
    if not 0.5 <= minimum_accuracy <= 1:
        raise ValueError("Minimum accuracy must be between 0.5 and 1.")
    if recording.duration < config.warmup_sec + config.window_sec:
        raise ValueError(f"Recording is only {recording.duration:.3f}s; at least "
                         f"{config.warmup_sec + config.window_sec:.3f}s is needed even "
                         "for one feature. Record the complete labeled protocol.")
    trials, alignment = align_trials(session, recording, offset_sec, settle_sec, trim_end_sec)
    repeats = sorted({t["repeat"] for t in trials})
    if len(repeats) < 2:
        raise ValueError("At least two complete repetitions are required.")
    # Split before parameter fitting; no overlapping window can cross a trial.
    held_out_repeat = repeats[-1]
    blink_learning = None
    if config.offline_detrend_sec and not config.blink_threshold_uv:
        boundary = min(t["onset_sec"] for t in trials if t["repeat"] == held_out_repeat)
        stop = int(boundary * recording.sfreq)
        score = blink_residual(recording.data[:, :stop], recording.sfreq,
                               config.balanced_vertical)
        times = np.arange(stop) / recording.sfreq
        clean_samples, blink_samples = [], []
        for trial in trials:
            if trial["repeat"] == held_out_repeat:
                continue
            mask = ((times >= trial["usable_start_sec"]) &
                    (times < trial["usable_end_sec"]) & np.isfinite(score))
            (blink_samples if trial["label"] == "BLINK" else clean_samples).extend(score[mask])
        if not clean_samples or not blink_samples:
            raise ValueError("Need finite stable and BLINK training samples for artifact handling.")
        clean_upper = float(np.quantile(clean_samples, 0.999))
        blink_upper = float(np.quantile(blink_samples, 0.99))
        threshold = max(20.0, clean_upper * 2.0)
        if blink_upper <= threshold:
            raise ValueError("Training BLINK pulses do not exceed stable-signal fluctuations; "
                             "cannot learn a reliable blink detector.")
        config = replace(config, blink_threshold_uv=threshold)
        blink_learning = {"threshold_uv": threshold, "stable_99_9_percentile_uv": clean_upper,
                          "blink_99_percentile_uv": blink_upper,
                          "source": "training repetitions only"}
    rows = labeled_features(recording, config, trials)
    if config.offline_detrend_sec:
        # The symmetric smoother must not use held-out samples to construct
        # training features. Test playback remains label-free and file-based.
        boundary = min(t["onset_sec"] for t in trials if t["repeat"] == held_out_repeat)
        training_recording = replace(
            recording, data=recording.data[:, :int(boundary * recording.sfreq)])
        training_trials = [t for t in trials if t["repeat"] != held_out_repeat]
        training_rows = labeled_features(training_recording, config, training_trials)
        rows = training_rows + [(f, t) for f, t in rows if t["repeat"] == held_out_repeat]
    for repeat in repeats:
        for label in LABELS:
            count = sum(t["repeat"] == repeat and t["label"] == label for _, t in rows)
            if count < 1:
                raise ValueError(f"Repeat {repeat + 1} / {label} has only {count} usable "
                                 "windows. At least one complete feature window is required. "
                                 "Extend holds, reduce missing data, or recollect.")
    for trial in trials:
        if not any(t["trial_id"] == trial["trial_id"] for _, t in rows):
            raise ValueError(f"Trial {trial['trial_id']} / {trial['label']} has no complete "
                             "usable window. Extend the hold or inspect missing data.")
    train = [(f, t) for f, t in rows if t["repeat"] != held_out_repeat]
    test = [(f, t) for f, t in rows if t["repeat"] == held_out_repeat]
    baseline, variance_limits, directions = fit_parameters(train, config, minimum_accuracy)
    model = {
        "schema_version": SCHEMA_VERSION, "processing_version": PROCESSING_VERSION,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "units": {"amplitude": "uV", "variance": "uV^2"},
        "sfreq_hz": recording.sfreq, "reference": reference.strip(),
        "reference_verification": "operator supplied; confirm acquisition settings",
        "processing": asdict(config), "baseline_uv": baseline,
        "variance_limits_uv2": variance_limits, "directions": directions,
        "channel_map": recording.metadata["channels"],
        "axes": {"horizontal": "F8 - F7", "vertical":
                 "(Fp1 + Fp2 - F7 - F8) / 2" if config.balanced_vertical
                 else "(Fp1 + Fp2) / 2"},
        "operating_mode": "offline_recording" if config.offline_detrend_sec else "causal_streaming",
        "feature_statistic": "median_and_scaled_MAD_squared" if config.robust_features
                             else "mean_and_variance",
        "source": recording.metadata,
        "session": {"session_id": session["session_id"], "screen": session.get("screen"),
                    "alignment": alignment, "held_out_repeat": held_out_repeat,
                    "settle_sec": settle_sec, "trim_end_sec": trim_end_sec},
    }
    quality = validation_report(test, model, minimum_accuracy)
    quality["behavior"] = behavior_report(recording, config, model, trials,
                                           held_out_repeat, minimum_accuracy)
    apply_acceptance(quality, acceptance_policy)
    if blink_learning:
        quality["blink_detection_training"] = blink_learning
    if config.offline_detrend_sec:
        quality["preprocessing_note"] = (
            "Training drift estimates use training samples only. Held-out recorded-file "
            "processing uses surrounding unlabeled samples, including future samples. "
            "These results do not validate live streaming or another recording.")
        quality["validation_scope"] = "exploratory within-recording validation; independent recording required"
    model["quality"] = quality
    if quality["passed"]:
        calibration_model(model)
    return model, rows, trials


def save_features(path, rows, held_out_repeat):
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["time_sec", "trial_id", "repeat", "label", "split",
                         "h_mean_uv", "v_mean_uv", "h_variance_uv2", "v_variance_uv2",
                         "blink_recent", "blink_fraction"])
        for feature, trial in rows:
            writer.writerow([feature.time_sec, trial["trial_id"], trial["repeat"],
                             trial["label"],
                             "validation" if trial["repeat"] == held_out_repeat else "training",
                             *feature.mean_uv, *feature.variance_uv2,
                             feature.blink_recent, feature.blink_fraction])


def save_diagnostics(path, rows, trials, model):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
    times = [f.time_sec for f, _ in rows]
    means = np.asarray([f.mean_uv for f, _ in rows]) - model["baseline_uv"]
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
    robust = model["processing"].get("robust_features", False)
    axes[0].set_ylabel("Centered " + ("median" if robust else "mean") + " (uV)")
    axes[1].set_ylabel("Scaled MAD squared (uV^2)" if robust else "Variance (uV^2)")
    axes[1].set_yscale("symlog", linthresh=1)
    axes[1].set_ylim(bottom=0)
    axes[1].set_xlabel("Time in recording (seconds)")
    for ax in axes:
        ax.legend(loc="upper right")
        ax.grid(alpha=0.2)
    quality = model["quality"]
    title = ("Recorded command calibration" if quality.get("acceptance_policy") == "command_trials"
             else "Calibration diagnostics")
    title += " — " + ("ACCEPTED" if quality["passed"] else "FAILED")
    if quality.get("acceptance_policy") == "command_trials" and not quality["window_checks_passed"]:
        title += " (continuous-window checks failed)"
    fig.suptitle(title)
    fig.tight_layout(rect=[0, 0, 1, 0.9])
    fig.savefig(path)
    plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("recording", help="ANT CNT or EDF recording")
    parser.add_argument("--session", required=True, help="Completed GUI session JSON")
    parser.add_argument("--reference", required=True, help="Reference used during acquisition")
    parser.add_argument("--output", default="output/calibration.json")
    alignment_group = parser.add_mutually_exclusive_group()
    alignment_group.add_argument("--offset", type=float, help="EEG time of FIRST target, seconds")
    alignment_group.add_argument("--offset-range", nargs=2, type=float, metavar=("MIN", "MAX"),
                                 help="Known timing bounds; use their midpoint and report uncertainty")
    parser.add_argument("--offline-drift", action="store_true",
                        help="Recorded-file profile: drift/blink correction, one-second median "
                        "features and three seconds of usable dwell evidence. Not for live LSL.")
    parser.add_argument("--command-calibration", action="store_true",
                        help="With --offline-drift, accept by held-gaze commands, majority trials, "
                        "neutral recall and blink coverage. Report continuous window failures.")
    parser.add_argument("--channel-map", help='JSON file mapping canonical names to recording labels')
    parser.add_argument("--settle", type=float, default=2.0)
    parser.add_argument("--trim-end", type=float, default=None)
    parser.add_argument("--lowpass", type=float, default=5.0)
    parser.add_argument("--highpass", type=float, default=None,
                        help="Optional cutoff; default preserves DC (low-pass only)")
    parser.add_argument("--warmup", type=float, default=2.0)
    parser.add_argument("--minimum-accuracy", type=float, default=0.8)
    parser.add_argument("--no-plot", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    output = Path(args.output)
    try:
        if args.command_calibration and not args.offline_drift:
            raise ValueError("--command-calibration requires --offline-drift.")
        if output.exists() and not args.overwrite:
            raise ValueError(f"{output} already exists; choose another path or use --overwrite.")
        mapping = read_json(args.channel_map) if args.channel_map else None
        recording = load_recording(args.recording, mapping)
        session = read_json(args.session)
        config = ProcessingConfig(lowpass_hz=args.lowpass, highpass_hz=args.highpass,
                                  warmup_sec=args.warmup,
                                  window_sec=1.0 if args.offline_drift else 3.0,
                                  offline_detrend_sec=10.0 if args.offline_drift else 0.0,
                                  balanced_vertical=args.offline_drift,
                                  hierarchical_axes=args.offline_drift,
                                  blink_pause_sec=1.0 if args.offline_drift else 0.0,
                                  robust_features=args.offline_drift)
        offset = args.offset
        trim_end = args.trim_end if args.trim_end is not None else (0.75 if args.offline_drift else 0.25)
        if args.offset_range:
            low, high = args.offset_range
            if not np.isfinite([low, high]).all() or low < 0 or high <= low:
                raise ValueError("Offset bounds must satisfy 0 <= MIN < MAX.")
            if high - low > 1.0:
                raise ValueError("Offset range is too wide; establish bounds within one second.")
            offset = (low + high) / 2
            trim_end = max(trim_end, (high - low) / 2 + 0.25)
            for bound in (low, high):
                align_trials(session, recording, bound, args.settle, trim_end)
        model, rows, trials = calibrate(
            recording, session, args.reference, config, offset,
            args.settle, trim_end, args.minimum_accuracy,
            "command_trials" if args.command_calibration else "all_states")
        if args.offset_range:
            config = ProcessingConfig(**model["processing"])
            model["session"]["alignment"] = {
                "method": "operator_bounded_offset", "offset_sec": offset,
                "bounds_sec": args.offset_range,
                "note": "Midpoint of user-provided bounds; not a measured stimulus onset."}
            sensitivity = {}
            for bound in args.offset_range:
                shifted_trials, _ = align_trials(session, recording, bound, args.settle, trim_end)
                shifted = [(f, t) for f, t in labeled_features(recording, config, shifted_trials)
                           if t["repeat"] == model["session"]["held_out_repeat"]]
                sensitivity[str(bound)] = validation_report(shifted, model, args.minimum_accuracy)
                sensitivity[str(bound)]["behavior"] = behavior_report(
                    recording, config, model, shifted_trials,
                    model["session"]["held_out_repeat"], args.minimum_accuracy)
                apply_acceptance(sensitivity[str(bound)], model["quality"]["acceptance_policy"])
            model["quality"]["alignment_sensitivity"] = sensitivity
            model["quality"]["passed"] = model["quality"]["passed"] and all(
                item["passed"] and item["behavior"]["passed"] for item in sensitivity.values())
        if args.command_calibration:
            model["quality"]["full_recording_audit"] = behavior_report(
                recording, ProcessingConfig(**model["processing"]), model, trials,
                None, args.minimum_accuracy)
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
        if args.offline_drift:
            print("Recorded-file processing only; live LSL use is blocked.")
        if args.command_calibration:
            print("Accepted for held-gaze commands. Continuous per-direction window checks "
                  f"passed: {model['quality']['window_checks_passed']}. See report for limitations.")
            audit = model["quality"]["full_recording_audit"]
            print(f"Full-recording audit: {audit['false_activation_count']} false activations; "
                  f"{audit['duplicate_correct_activation_count']} duplicate correct activations. "
                  "Exploratory use; validate on an independent recording.")
        print(json.dumps(model["quality"]["per_class"], indent=2))
        return 0
    except (ValueError, KeyError, TypeError, OSError, ImportError, RuntimeError) as exc:
        parser.exit(2, f"Calibration failed: {exc}\n")


if __name__ == "__main__":
    main()
