"""Drift tracking and direction-subset calibration (added for the Nov 7 session 2 recording)."""
from copy import deepcopy
import unittest

import numpy as np

from calibration import calibrate
from eog_pipeline import (
    DwellClassifier, Feature, ProcessingConfig, calibration_model, candidate_for,
)
from tests.synthetic import make_session


class DriftAndSubsetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recording, cls.session = make_session()
        # Slow electrode drift, bigger than any gaze step, on the horizontal and vertical axes.
        cls.drifting = deepcopy(cls.recording)
        drift = np.linspace(0, 250e-6, cls.drifting.data.shape[1])
        cls.drifting.data[1] += drift
        cls.drifting.data[2] += drift / 2
        cls.drifting.data[3] += drift / 2

    def test_drift_breaks_fixed_baseline_but_tracking_recovers(self):
        with self.assertRaisesRegex(ValueError, "not separable"):
            calibrate(self.drifting, self.session, "CPz", offset_sec=0)
        model, rows, _ = calibrate(self.drifting, self.session, "CPz",
                                   ProcessingConfig(baseline_track_sec=3.0), offset_sec=0)
        self.assertTrue(model["quality"]["passed"])
        self.assertEqual(model["quality"]["behavior"]["false_activation_count"], 0)
        self.assertTrue(all(f.baseline_uv is not None for f, _ in rows))
        self.assertEqual(model["processing"]["baseline_track_sec"], 3.0)

    def test_horizontal_only_calibration(self):
        model, _, _ = calibrate(self.recording, self.session, "CPz", offset_sec=0,
                                directions=("RIGHT", "LEFT"))
        self.assertEqual(set(model["directions"]), {"RIGHT", "LEFT"})
        self.assertTrue(model["quality"]["passed"])
        self.assertEqual(set(model["quality"]["per_class"]), {"CENTER", "RIGHT", "LEFT"})
        calibration_model(model)
        # Vertical variance (a blink) no longer blocks a horizontal decision.
        mean = list(model["baseline_uv"])
        rule = model["directions"]["RIGHT"]
        mean[0] += rule["polarity"] * rule["threshold_uv"] * 1.5
        feature = Feature(10.0, 0, "OK", mean, [0.0, 1e9], mean, 7.0)
        self.assertEqual(candidate_for(feature, model), "RIGHT")
        with self.assertRaisesRegex(ValueError, "subset"):
            calibrate(self.recording, self.session, "CPz", offset_sec=0,
                      directions=("RIGHT", "SIDEWAYS"))

    def test_settling_repetition_can_be_skipped(self):
        settling = deepcopy(self.recording)
        first = [t for t in calibrate(self.recording, self.session, "CPz", offset_sec=0)[2]
                 if t["repeat"] == 0]
        start = round(min(t["onset_sec"] for t in first) * settling.sfreq)
        stop = round(max(t["end_sec"] for t in first) * settling.sfreq)
        settling.data[1, start:stop] += np.linspace(300e-6, 0, stop - start)  # fast early drift
        with self.assertRaisesRegex(ValueError, "not separable"):
            calibrate(settling, self.session, "CPz", offset_sec=0)
        model, _, trials = calibrate(settling, self.session, "CPz", offset_sec=0,
                                     skip_repeats=1)
        self.assertTrue(model["quality"]["passed"])
        self.assertEqual(model["session"]["skipped_repeats"], 1)
        self.assertEqual(min(t["repeat"] for t in trials), 1)
        with self.assertRaisesRegex(ValueError, "At least two"):
            calibrate(settling, self.session, "CPz", offset_sec=0, skip_repeats=2)

    def test_live_tracker_starts_from_first_window_and_rescues_runaway_holds(self):
        model, _, _ = calibrate(
            self.recording, self.session, "CPz",
            ProcessingConfig(baseline_track_sec=2.0, baseline_rescue_sec=12.0), offset_sec=0)
        engine = DwellClassifier(model)  # rescue must exceed the protocol's 10 s holds
        far = (np.asarray(model["baseline_uv"]) + [500.0, 0.0]).tolist()  # today's DC level
        out = engine.update(Feature(3.0, 0, "OK", far, [0.0, 0.0], far, 0.0))
        self.assertEqual(out["state"], "CENTER")
        self.assertAlmostEqual(out["h_baseline_uv"], far[0])
        rule = model["directions"]["RIGHT"]
        gaze = list(far)
        gaze[0] += rule["polarity"] * rule["threshold_uv"] * 1.5
        states = [engine.update(Feature(3.0 + i / 10, 0, "OK", gaze, [0.0, 0.0], gaze,
                                        i / 10))["state"] for i in range(1, 160)]
        self.assertIn("RIGHT", states)
        self.assertIn("RECENTERED", states)
        self.assertEqual(states[-1], "CENTER")
        with self.assertRaisesRegex(ValueError, "requires"):
            ProcessingConfig(baseline_rescue_sec=6.0).validate(100)

    def test_tracker_follows_center_and_freezes_during_gaze(self):
        model, _, _ = calibrate(self.recording, self.session, "CPz",
                                ProcessingConfig(baseline_track_sec=1.0), offset_sec=0)
        engine = DwellClassifier(model)
        base = np.asarray(model["baseline_uv"])
        shifted = (base + [20.0, 0.0]).tolist()  # electrodes drifted 20 uV, gaze still centred
        for i in range(60):
            out = engine.update(Feature(i / 10, 0, "OK", shifted, [0.0, 0.0], shifted,
                                        max(0.0, i / 10 - 3)))
        self.assertEqual(out["state"], "CENTER")
        self.assertAlmostEqual(out["h_baseline_uv"], base[0] + 20, delta=0.5)
        rule = model["directions"]["RIGHT"]
        gaze = list(shifted)
        gaze[0] += rule["polarity"] * rule["threshold_uv"] * 1.5
        frozen = out["h_baseline_uv"]
        for i in range(60, 100):
            out = engine.update(Feature(i / 10, 0, "OK", gaze, [0.0, 0.0], gaze, i / 10 - 3))
        self.assertEqual(out["state"], "RIGHT")
        self.assertEqual(out["h_baseline_uv"], frozen)


if __name__ == "__main__":
    unittest.main()
