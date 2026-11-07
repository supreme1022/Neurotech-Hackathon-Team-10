from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from calibration import calibrate, main as calibration_main, labeled_features
from calibration_session import align_trials, build_protocol
from eog_pipeline import (
    CHANNELS, DwellClassifier, Feature, FeatureStream, ProcessingConfig,
    Recording, analyze_recording, calibration_model, candidate_for,
    channel_indices, check_compatibility, read_json, write_json,
)
from lsl_input import LSLSource, unit_scale
from real_time_classification import ResultSink, run_live, run_playback
from tests.synthetic import make_session


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recording, cls.session = make_session()
        cls.model, cls.rows, cls.trials = calibrate(
            cls.recording, cls.session, "CPz", offset_sec=0)

    def test_whole_pipeline_and_polarity(self):
        model = self.model
        self.assertTrue(model["quality"]["passed"])
        self.assertTrue(model["quality"]["behavior"]["passed"])
        self.assertEqual(model["quality"]["behavior"]["false_activation_count"], 0)
        self.assertEqual(model["directions"]["RIGHT"]["polarity"], -1)
        self.assertEqual(model["directions"]["UP"]["polarity"], -1)
        np.testing.assert_allclose(model["baseline_uv"], [20, 35], atol=0.1)
        self.assertEqual(model["units"]["variance"], "uV^2")
        for item in model["quality"]["per_class"].values():
            self.assertEqual(item["recall"], 1.0)
        self.assertEqual(model["session"]["held_out_repeat"], 2)

    def test_chunk_boundaries_do_not_change_features(self):
        cfg = ProcessingConfig()
        data = self.recording.data[:, :1600]
        times = np.arange(data.shape[1]) / self.recording.sfreq
        expected = list(FeatureStream(100, cfg).push(data, times))
        stream = FeatureStream(100, cfg)
        actual = []
        for first in range(0, len(times), 37):
            actual.extend(stream.push(data[:, first:first + 37], times[first:first + 37]))
        self.assertEqual(len(expected), len(actual))
        for a, b in zip(expected, actual):
            self.assertEqual(a.time_sec, b.time_sec)
            self.assertEqual(a.quality, b.quality)
            if a.quality == "OK":
                np.testing.assert_allclose(a.mean_uv, b.mean_uv, atol=1e-10)
                np.testing.assert_allclose(a.variance_uv2, b.variance_uv2, atol=1e-10)

    def test_invalid_samples_and_timestamp_gaps_reset_history(self):
        stream = FeatureStream(100)
        data = np.zeros((4, 1000))
        data[:, 600:610] = np.nan
        times = np.arange(1000) / 100
        times[800:] += 1
        rows = list(stream.push(data, times))
        self.assertTrue(any(f.quality == "OK" and f.time_sec < 6 for f in rows))
        self.assertTrue(any(f.quality == "INVALID" for f in rows))
        self.assertTrue(any(f.quality == "GAP" for f in rows))
        self.assertFalse(any(f.quality == "OK" and f.time_sec >= 6 for f in rows))
        with self.assertRaisesRegex(ValueError, "out of order"):
            list(stream.push(np.zeros((4, 2)), [1, 2]))

    def test_no_feature_contains_warmup_samples(self):
        rows = list(FeatureStream(100).push(np.zeros((4, 600)), np.arange(600) / 100))
        first = next(f for f in rows if f.quality == "OK")
        self.assertAlmostEqual(first.window_start_sec, 2.0)
        self.assertAlmostEqual(first.time_sec, 4.99)

    def test_alignment_requires_evidence(self):
        with self.assertRaisesRegex(ValueError, "Cannot align"):
            align_trials(self.session, self.recording)
        with self.assertRaisesRegex(ValueError, "only"):
            align_trials(self.session, self.recording, offset_sec=20)
        incomplete = deepcopy(self.session)
        incomplete["status"] = "aborted"
        with self.assertRaisesRegex(ValueError, "complete"):
            align_trials(incomplete, self.recording, offset_sec=0)

    def test_verified_annotation_alignment(self):
        recording = deepcopy(self.recording)
        recording.annotations = [
            {"description": e["marker"], "onset_sec": e["onset_sec"]}
            for e in self.session["events"]
        ] + [{"description": self.session["end_marker"], "onset_sec": recording.duration}]
        trials, alignment = align_trials(self.session, recording)
        self.assertEqual(alignment["method"], "acquisition_markers")
        self.assertEqual(len(trials), len(self.trials))
        recording.annotations.append(recording.annotations[1])
        with self.assertRaisesRegex(ValueError, "duplicated"):
            align_trials(self.session, recording)

    def test_short_and_missing_trials_fail(self):
        short = Recording(self.recording.data[:, :285], 100,
                          self.recording.metadata, [])
        with self.assertRaisesRegex(ValueError, "only 2.850"):
            calibrate(short, self.session, "CPz", offset_sec=0)
        session = deepcopy(self.session)
        for event in session["events"]:
            if event["label"] == "BLINK":
                event["label"] = "CENTER"
        with self.assertRaisesRegex(ValueError, "BLINK"):
            calibrate(self.recording, session, "CPz", offset_sec=0)

    def test_no_window_crosses_trial_or_settling_boundaries(self):
        for feature, trial in self.rows:
            self.assertGreaterEqual(feature.window_start_sec + 1e-9,
                                    trial["usable_start_sec"])
            self.assertLessEqual(feature.time_sec + 0.01,
                                 trial["usable_end_sec"] + 1e-9)

    def test_holdout_changes_do_not_change_training_parameters(self):
        altered = deepcopy(self.recording)
        start = min(t["onset_sec"] for t in self.trials if t["repeat"] == 2)
        altered.data[1, round(start * altered.sfreq):] += 200e-6
        model, _, _ = calibrate(altered, self.session, "CPz", offset_sec=0)
        self.assertEqual(model["directions"], self.model["directions"])
        self.assertEqual(model["baseline_uv"], self.model["baseline_uv"])
        self.assertFalse(model["quality"]["passed"])

    def test_inseparable_vertical_data_fails(self):
        data = deepcopy(self.recording)
        data.data[2:] = 35e-6
        with self.assertRaisesRegex(ValueError, "not separable"):
            calibrate(data, self.session, "CPz", offset_sec=0)

    def test_artifact_and_compatibility_validation(self):
        model = deepcopy(self.model)
        model["quality"]["passed"] = False
        with self.assertRaisesRegex(ValueError, "quality"):
            calibration_model(model)
        with self.assertRaisesRegex(ValueError, "Sampling rate"):
            check_compatibility(self.model, 1000, "CPz")
        with self.assertRaisesRegex(ValueError, "reference"):
            check_compatibility(self.model, 100, "Cz")
        check_compatibility(self.model, 100, "cpz")
        model = deepcopy(self.model)
        model["directions"]["RIGHT"]["threshold_uv"] = float("nan")
        with self.assertRaisesRegex(ValueError, "finite"):
            calibration_model(model)

    def direction_feature(self, time, generation=0, variance=0):
        mean = np.asarray(self.model["baseline_uv"]).copy()
        rule = self.model["directions"]["RIGHT"]
        mean[0] += rule["polarity"] * rule["threshold_uv"] * 1.5
        return Feature(time, generation, "OK", mean.tolist(), [variance, variance],
                       mean.tolist(), max(0, time - 3))

    def test_dwell_blink_reset_and_single_activation(self):
        engine = DwellClassifier(self.model)
        rows = [engine.update(self.direction_feature(i / 10)) for i in range(41)]
        self.assertEqual(rows[29]["state"], "DWELLING")
        self.assertEqual(rows[30]["state"], "RIGHT")
        self.assertEqual(sum(row["activated"] for row in rows), 1)
        blink = engine.update(self.direction_feature(4.1, variance=1e9))
        self.assertEqual(blink["state"], "TRANSITION_BLINK")
        self.assertEqual(engine.update(self.direction_feature(4.2))["dwell_sec"], 0)

    def test_recent_disagreement_and_gap_cancel_dwell(self):
        engine = DwellClassifier(self.model)
        for i in range(25):
            engine.update(self.direction_feature(i / 10))
        feature = self.direction_feature(2.5)
        feature.recent_mean_uv = self.model["baseline_uv"]
        self.assertEqual(engine.update(feature)["state"], "TRANSITION")
        self.assertEqual(engine.update(self.direction_feature(2.6))["dwell_sec"], 0)
        self.assertEqual(engine.update(self.direction_feature(3.5))["dwell_sec"], 0)
        self.assertEqual(engine.update(self.direction_feature(3.6, generation=1))["dwell_sec"], 0)

    def test_ambiguous_gaze_never_selects_horizontal_by_priority(self):
        feature = self.direction_feature(0)
        rule = self.model["directions"]["UP"]
        feature.mean_uv[1] += rule["polarity"] * rule["threshold_uv"] * 2
        feature.recent_mean_uv = feature.mean_uv
        self.assertEqual(candidate_for(feature, self.model), "AMBIGUOUS")

    def test_channel_names_and_units(self):
        self.assertEqual(channel_indices([" fp1 ", "fp2", "f8", "f7"]), [3, 2, 0, 1])
        self.assertEqual(channel_indices(["a", "b", "c", "d"],
                                        dict(zip(CHANNELS, ["a", "b", "c", "d"]))),
                         [0, 1, 2, 3])
        with self.assertRaises(ValueError):
            channel_indices(["F7", "F7", "Fp1", "Fp2", "F8"])
        with self.assertRaises(ValueError):
            channel_indices(["F7", "F8", "Fp1"])
        self.assertEqual(unit_scale("uV"), 1e-6)
        self.assertEqual(unit_scale("\u00b5V"), 1e-6)
        self.assertEqual(unit_scale("V"), 1)
        with self.assertRaises(ValueError):
            unit_scale("ADC counts")

    def test_protocol_and_config_validation(self):
        with self.assertRaises(ValueError):
            build_protocol(repetitions=1)
        for cfg in (ProcessingConfig(lowpass_hz=100),
                    ProcessingConfig(highpass_hz=-1),
                    ProcessingConfig(warmup_sec=float("nan"))):
            with self.assertRaises(ValueError):
                cfg.validate(100)

    def test_json_roundtrip_and_playback_results(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "calibration.json"
            write_json(path, self.model)
            self.assertEqual(calibration_model(read_json(path)), self.model)
            csv_path = Path(directory) / "predictions.csv"
            sink = ResultSink(csv_path, self.model, self.recording.metadata)
            with patch("builtins.print"):
                run_playback(self.recording, self.model, sink, speed=0)
            sink.close("complete")
            summary = read_json(csv_path.with_suffix(".summary.json"))
            self.assertEqual(summary["status"], "complete")
            for direction in ("RIGHT", "LEFT", "UP", "DOWN"):
                self.assertGreaterEqual(summary["activation_counts"].get(direction, 0), 3)
            with self.assertRaises(FileExistsError):
                ResultSink(csv_path, self.model, {})
            with self.assertRaises(ValueError):
                write_json(Path(directory) / "nan.json", {"bad": float("nan")})

    def test_failed_calibration_does_not_write_usable_model(self):
        altered = deepcopy(self.recording)
        start = min(t["onset_sec"] for t in self.trials if t["repeat"] == 2)
        altered.data[1, round(start * altered.sfreq):] += 200e-6
        with tempfile.TemporaryDirectory() as directory:
            session_path = Path(directory) / "session.json"
            output = Path(directory) / "model.json"
            write_json(session_path, self.session)
            with patch("calibration.load_recording", return_value=altered):
                with self.assertRaises(SystemExit) as error:
                    calibration_main(["fake.cnt", "--session", str(session_path),
                                      "--reference", "CPz", "--offset", "0",
                                      "--output", str(output), "--no-plot"])
            self.assertEqual(error.exception.code, 2)
            self.assertFalse(output.exists())
            self.assertFalse(read_json(output.with_suffix(".report.json"))["quality"]["passed"])

    def test_lsl_adapter_metadata_and_scaling(self):
        class Node:
            index = 0
            def child(self, name):
                return self
            def child_value(self, key):
                return CHANNELS[self.index] if key == "label" else "uV"
            def next_sibling(self):
                result = Node()
                result.index = self.index + 1
                return result
        class Info:
            def nominal_srate(self): return 100
            def channel_count(self): return 4
            def desc(self): return Node()
            def name(self): return "fake"
            def source_id(self): return "test"
        class Inlet:
            def __init__(self, *args, **kwargs): pass
            def info(self, **kwargs): return Info()
            def close_stream(self): pass
            def pull_chunk(self, **kwargs): return [[1, 2, 3, 4]], [10.0]
        import types
        fake = types.SimpleNamespace(
            resolve_byprop=lambda *a, **k: [Info()], StreamInlet=Inlet,
            proc_clocksync=1, local_clock=lambda: 10)
        with patch.dict("sys.modules", {"pylsl": fake}):
            source = LSLSource(stream_name="fake")
            data, times = source.pull()
            np.testing.assert_allclose(data[:, 0], np.array([1, 2, 3, 4]) * 1e-6)
            self.assertEqual(times[0], 10)
            source.close()

    def test_live_stale_samples_are_discarded(self):
        class FakeSource:
            sfreq = 100
            calls = 0
            def pull(self):
                self.calls += 1
                if self.calls == 1:
                    return np.zeros((4, 10)), np.arange(10) / 100
                raise RuntimeError("finished")
            def clock(self): return 10.0
        class Sink:
            def emit(self, result):
                raise AssertionError("Stale initial data should never be classified")
        with self.assertRaisesRegex(RuntimeError, "finished"):
            run_live(FakeSource(), self.model, Sink())

    def test_repository_cnt_is_rejected_as_too_short(self):
        path = Path(__file__).resolve().parents[1] / "Team10_Session1_2026-11-07_15-31-01.cnt"
        if not path.exists():
            self.skipTest("Local CNT fixture is not distributed.")
        from eog_pipeline import load_recording
        recording = load_recording(path)
        self.assertAlmostEqual(recording.duration, 2.855, places=3)
        self.assertEqual(recording.data.shape, (4, 2855))
        with self.assertRaisesRegex(ValueError, "only 2.855"):
            calibrate(recording, self.session, "CPz", offset_sec=0)


    def test_gui_completion_and_abort_logs_without_opening_a_window(self):
        from calibration_GUI import CalibrationGUI

        class Widget:
            def __init__(self, *args, **kwargs): pass
            def pack(self, **kwargs): pass
            def configure(self, **kwargs): pass
            def delete(self, *args): pass
            def create_text(self, *args, **kwargs): return 1
            def create_oval(self, *args, **kwargs): return 2
        class Variable:
            def __init__(self, **kwargs): self.value = kwargs.get("value")
            def get(self): return self.value
            def set(self, value): self.value = value
        class Root:
            def title(self, *args): pass
            def attributes(self, *args): pass
            def configure(self, **kwargs): pass
            def bind(self, *args): pass
            def unbind(self, *args): pass
            def protocol(self, *args): pass
            def update_idletasks(self): pass
            def after(self, *args): return "scheduled"
            def after_cancel(self, *args): pass
            def destroy(self): pass

        clock = [100.0]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "session.json"
            with patch("calibration_GUI.tk.Canvas", Widget), \
                    patch("calibration_GUI.tk.Checkbutton", Widget), \
                    patch("calibration_GUI.tk.BooleanVar", Variable), \
                    patch("calibration_GUI.time.perf_counter", side_effect=lambda: clock[0]):
                gui = CalibrationGUI(Root(), path, countdown_sec=0, fullscreen=False)
                gui.confirmed.set(True)
                gui.start_protocol()
                for trial in gui.protocol:
                    clock[0] += trial["duration_sec"]
                    gui.run_step()
                session = read_json(path)
                self.assertEqual(session["status"], "complete")
                self.assertEqual(len(session["events"]), len(gui.protocol))
                self.assertEqual(session["events"][0]["onset_sec"], 0)
                self.assertTrue(all(e["duration_sec"] > 0 for e in session["events"]))
                _, alignment = align_trials(session, self.recording, offset_sec=0)
                self.assertEqual(alignment["method"], "operator_verified_offset")
                aborted_path = Path(directory) / "aborted.json"
                aborted = CalibrationGUI(Root(), aborted_path, fullscreen=False)
                aborted.close()
                self.assertEqual(read_json(aborted_path)["status"], "aborted")



    def test_edf_roundtrip_produces_json_serializable_calibration(self):
        from eog_pipeline import load_recording
        from tests.synthetic import write_edf

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "recording.edf"
            write_edf(self.recording, path)
            loaded = load_recording(path)
            self.assertEqual(loaded.data.shape, self.recording.data.shape)
            np.testing.assert_allclose(loaded.data, self.recording.data, atol=0.016e-6)
            model, _, _ = calibrate(loaded, self.session, "CPz", offset_sec=0)
            self.assertTrue(model["quality"]["passed"])
            write_json(Path(directory) / "calibration.json", model)
            self.assertIsInstance(model["source"]["samples"], int)


if __name__ == "__main__":
    unittest.main()
