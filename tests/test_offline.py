"""Checks for recorded-file drift correction and explicit artifact pauses."""
from copy import deepcopy
from dataclasses import asdict
import unittest
from unittest.mock import patch

import numpy as np

from calibration import calibrate, validation_report, apply_acceptance, behavior_report
from eog_pipeline import (
    CHANNELS, PROCESSING_VERSION, SCHEMA_VERSION, DwellClassifier, Feature,
    FeatureStream, ProcessingConfig, Recording, analyze_recording,
    calibration_model, candidate_for, detrend_recording,
)
from tests.synthetic import make_session


def model_for(config=None):
    config = config or ProcessingConfig()
    return {
        "schema_version": SCHEMA_VERSION, "processing_version": PROCESSING_VERSION,
        "processing": asdict(config), "reference": "CPz", "sfreq_hz": 100,
        "units": {"amplitude": "uV", "variance": "uV^2"},
        "quality": {"passed": True}, "baseline_uv": [0, 0],
        "variance_limits_uv2": [100, 100],
        "directions": {
            name: {"axis": axis, "polarity": sign, "threshold_uv": 10}
            for name, axis, sign in [("RIGHT", 0, 1), ("LEFT", 0, -1),
                                     ("UP", 1, 1), ("DOWN", 1, -1)]},
    }


def feature_at(t, blink=False, generation=0, mean=None):
    mean = [20, 0] if mean is None else mean
    return Feature(t, generation, "OK", mean, [1, 1], mean, max(0, t - 1), blink,
                   0.1 if blink else 0.0)


class OfflineTests(unittest.TestCase):
    def test_full_recording_audit_includes_training_errors_and_duplicates(self):
        class Classifier:
            def __init__(self, model): pass
            def update(self, feature): return {"activated": True, "state": "RIGHT"}
        trials = [
            {"trial_id": "a", "repeat": 0, "label": "CENTER", "onset_sec": 0, "end_sec": 10},
            {"trial_id": "b", "repeat": 0, "label": "RIGHT", "onset_sec": 10, "end_sec": 20},
            {"trial_id": "c", "repeat": 1, "label": "RIGHT", "onset_sec": 20, "end_sec": 30},
        ]
        recording = Recording(np.zeros((4, 1)), 100, {}, [])
        features = [feature_at(t) for t in (2, 12, 21, 22)]
        with patch("eog_pipeline.DwellClassifier", Classifier), \
                patch("calibration.analyze_recording", return_value=features):
            full = behavior_report(recording, ProcessingConfig(), model_for(), trials, None, 0.8)
            held = behavior_report(recording, ProcessingConfig(), model_for(), trials, 1, 0.8)
        self.assertEqual(full["false_activation_count"], 1)
        self.assertEqual(held["false_activation_count"], 0)
        self.assertEqual(full["duplicate_correct_activation_count"], 1)
        self.assertFalse(full["passed"])
        self.assertTrue(held["passed"])

    def test_command_policy_reports_window_failure_without_hiding_it(self):
        quality = {
            "passed": False, "minimum_required_recall": 0.8,
            "held_out_trial_accuracy": 0.9,
            "per_class": {label: {"windows": 10, "recall": 0.9}
                          for label in ("CENTER", "RIGHT", "LEFT", "UP", "DOWN", "BLINK")},
            "behavior": {"passed": True, "false_activation_count": 0},
        }
        quality["per_class"]["UP"]["recall"] = 0.6
        strict = apply_acceptance(deepcopy(quality))
        commands = apply_acceptance(deepcopy(quality), "command_trials")
        self.assertFalse(strict["passed"])
        self.assertTrue(commands["passed"])
        self.assertFalse(commands["window_checks_passed"])
        self.assertEqual(commands["per_class"]["UP"]["recall"], 0.6)
        quality["behavior"]["false_activation_count"] = 1
        self.assertFalse(apply_acceptance(quality, "command_trials")["passed"])

    def test_legacy_model_cannot_enable_new_feature_modes(self):
        model = model_for()
        model["processing_version"] = "causal-eog-v1"
        calibration_model(model)
        model["processing"]["robust_features"] = True
        with self.assertRaisesRegex(ValueError, "Legacy"):
            calibration_model(model)

    def test_offline_mode_cannot_run_direct_stream(self):
        with self.assertRaisesRegex(ValueError, "cannot classify a live"):
            FeatureStream(100, ProcessingConfig(offline_detrend_sec=10))

    def test_detrending_is_invariant_to_dc_offsets_and_keeps_gaps(self):
        sfreq = 100
        times = np.arange(2000) / sfreq
        data = np.tile(times * 1e-6, (4, 1))
        data[:, 900:1000] = np.nan
        centered, mask = detrend_recording(data, sfreq, 3)
        shifted, _ = detrend_recording(data + 0.01, sfreq, 3)
        np.testing.assert_allclose(centered, shifted, atol=1e-15, equal_nan=True)
        self.assertTrue(np.isnan(centered[:, 900:1000]).all())
        self.assertFalse(mask.any())

    def test_blink_mask_removes_full_pulse_and_retains_metadata(self):
        sfreq = 100
        t = np.arange(2000) / sfreq
        data = np.zeros((4, len(t)))
        pulse = 300e-6 * np.exp(-0.5 * ((t - 10) / 0.08) ** 2)
        data[2:] = pulse
        clean, mask = detrend_recording(data, sfreq, 3, 30, balanced=True)
        self.assertTrue(mask[1000])
        self.assertFalse(mask[500])
        self.assertLess(np.max(np.abs(clean)), np.max(np.abs(data)) / 5)

    def test_robust_location_rejects_a_short_large_outlier(self):
        data = np.zeros((4, 400))
        data[1, 150:170] = 500e-6
        times = np.arange(400) / 100
        plain = list(FeatureStream(100, ProcessingConfig(warmup_sec=0)).push(data, times))
        robust = list(FeatureStream(100, ProcessingConfig(
            warmup_sec=0, robust_features=True)).push(data, times))
        self.assertLess(abs(robust[29].mean_uv[0]), abs(plain[29].mean_uv[0]) / 10)

    def test_blink_pause_does_not_count_as_dwell_or_emit_activation(self):
        engine = DwellClassifier(model_for(ProcessingConfig(blink_pause_sec=0.8)))
        results = []
        for i in range(36):
            results.append(engine.update(feature_at(i / 10, blink=20 <= i <= 23)))
        self.assertTrue(all(not r["activated"] for r in results[20:24]))
        self.assertEqual(results[33]["state"], "DWELLING")
        self.assertEqual(results[34]["state"], "RIGHT")
        self.assertEqual(sum(r["activated"] for r in results), 1)

    def test_long_blink_and_direction_change_reset_dwell(self):
        engine = DwellClassifier(model_for(ProcessingConfig(blink_pause_sec=0.5)))
        for i in range(20):
            engine.update(feature_at(i / 10))
        for i in range(20, 29):
            engine.update(feature_at(i / 10, blink=True))
        self.assertEqual(engine.update(feature_at(2.9))["dwell_sec"], 0)
        engine.update(feature_at(3.0, blink=True))
        self.assertEqual(engine.update(feature_at(3.1, mean=[-20, 0]))["dwell_sec"], 0)

    def test_unrelated_vertical_variance_does_not_veto_horizontal_gaze(self):
        model = model_for(ProcessingConfig(hierarchical_axes=True))
        feature = feature_at(0)
        feature.variance_uv2 = [1, 1000]
        self.assertEqual(candidate_for(feature, model), "RIGHT")
        feature.variance_uv2 = [1000, 1]
        self.assertEqual(candidate_for(feature, model), "TRANSITION_BLINK")

    def test_current_blink_exclusions_are_reported(self):
        config = ProcessingConfig(offline_detrend_sec=10, blink_threshold_uv=30)
        model = model_for(config)
        rows = [(feature_at(1), {"label": "RIGHT", "trial_id": "r"}),
                (feature_at(2, blink=True), {"label": "RIGHT", "trial_id": "r"}),
                (feature_at(3, blink=True), {"label": "BLINK", "trial_id": "b"})]
        report = validation_report(rows, model, 0.8)
        self.assertEqual(report["per_class"]["RIGHT"]["excluded_current_blink_windows"], 1)
        self.assertEqual(report["per_class"]["RIGHT"]["eligible_fraction"], 0.5)
        self.assertEqual(report["per_class"]["BLINK"]["recall"], 1)

    def test_held_out_data_cannot_change_offline_training_parameters(self):
        recording, session = make_session()
        config = ProcessingConfig(offline_detrend_sec=10, balanced_vertical=True,
                                  hierarchical_axes=True, robust_features=True,
                                  window_sec=1, blink_pause_sec=1)
        model, _, trials = calibrate(recording, session, "CPz", config, offset_sec=0,
                                     trim_end_sec=0.75)
        changed = deepcopy(recording)
        boundary = min(t["onset_sec"] for t in trials if t["repeat"] == 2)
        changed.data[:, int(boundary * changed.sfreq):] += np.array(
            [0, 200e-6, 70e-6, 0])[:, None]
        other, _, _ = calibrate(changed, session, "CPz", config, offset_sec=0,
                               trim_end_sec=0.75)
        self.assertEqual(model["directions"], other["directions"])
        self.assertEqual(model["baseline_uv"], other["baseline_uv"])
        self.assertEqual(model["processing"], other["processing"])


if __name__ == "__main__":
    unittest.main()
