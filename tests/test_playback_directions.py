from contextlib import redirect_stderr, redirect_stdout
import io
import json
import unittest
from unittest.mock import patch

import numpy as np

from eog_pipeline import Recording
from playback_directions import (
    DirectionEvent, main, prepare_directions, print_direction, replay_directions,
)
from tests.test_offline import feature_at, model_for


class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.waits = []

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.waits.append(seconds)
        self.now += seconds


class PrintedPlaybackTests(unittest.TestCase):
    def setUp(self):
        self.recording = Recording(np.zeros((4, 1200)), 100, {}, [])
        self.model = model_for()

    def test_commands_emit_only_after_dwell_once_per_activation(self):
        features = [feature_at(i / 10) for i in range(41)]
        features += [feature_at(4.1, blink=True)]
        features += [feature_at(i / 10, mean=[-20, 0]) for i in range(42, 75)]
        with patch("playback_directions.analyze_recording", return_value=features):
            events = prepare_directions(self.recording, self.model)
        self.assertEqual([e.direction for e in events], ["right", "left"])
        self.assertEqual([e.sequence for e in events], [1, 2])
        self.assertAlmostEqual(events[0].time_sec, 3.0)
        self.assertAlmostEqual(events[1].time_sec, 7.2)

    def test_labels_are_periodic_and_silent_for_neutral_or_blinks(self):
        features = [feature_at(i / 10) for i in range(21)]
        features += [feature_at(2.1, blink=True), feature_at(2.2, blink=True)]
        features += [feature_at(i / 10) for i in range(23, 35)]
        features += [feature_at(3.5, mean=[0, 0])]
        features += [feature_at(3.6, mean=[-20, 0])]
        with patch("playback_directions.analyze_recording", return_value=features):
            events = prepare_directions(self.recording, self.model, mode="labels")
        self.assertEqual([round(e.time_sec, 1) for e in events], [0, 1, 2, 2.3, 3.3, 3.6])
        self.assertEqual(events[-1].direction, "left")
        self.assertFalse(any(e.time_sec in (2.1, 2.2, 3.5) for e in events))

    def test_labels_do_not_print_retained_candidate_during_blink_pause(self):
        model = model_for()
        model["processing"]["blink_pause_sec"] = 0.8
        features = [feature_at(i / 10) for i in range(20)]
        features += [feature_at(i / 10, blink=True) for i in range(20, 24)]
        with patch("playback_directions.analyze_recording", return_value=features):
            events = prepare_directions(self.recording, model, mode="labels", interval_sec=0.1)
        self.assertTrue(events)
        self.assertLess(max(e.time_sec for e in events), 2)

    def test_clock_uses_recording_deadlines_not_accumulated_callback_delays(self):
        clock = FakeClock()
        observed = []
        events = [DirectionEvent(1, 2, "right", "commands"),
                  DirectionEvent(2, 4, "left", "commands")]

        def callback(event):
            observed.append((clock.now, event.direction))
            clock.now += 0.25

        replay_directions(events, 6, callback, clock=clock.clock, sleep=clock.sleep)
        self.assertAlmostEqual(observed[0][0], 2)
        self.assertAlmostEqual(observed[1][0], 4)
        self.assertAlmostEqual(clock.now, 6)
        self.assertTrue(all(0 < wait <= 0.05 for wait in clock.waits))

    def test_speed_and_silent_tail_are_preserved(self):
        clock = FakeClock()
        times = []
        replay_directions([DirectionEvent(1, 4, "up", "commands")], 8,
                          lambda event: times.append(clock.now), speed=2,
                          clock=clock.clock, sleep=clock.sleep)
        self.assertAlmostEqual(times[0], 2)
        self.assertAlmostEqual(clock.now, 4)
        clock = FakeClock()
        replay_directions([], 2, lambda event: self.fail("Unexpected event"),
                          clock=clock.clock, sleep=clock.sleep)
        self.assertAlmostEqual(clock.now, 2)

    def test_unpaced_playback_never_sleeps(self):
        clock = FakeClock()
        directions = []
        replay_directions([DirectionEvent(1, 4, "down", "commands")], 8,
                          lambda event: directions.append(event.direction), speed=0,
                          clock=clock.clock, sleep=clock.sleep)
        self.assertEqual(directions, ["down"])
        self.assertFalse(clock.waits)

    def test_text_timestamp_and_json_formats(self):
        event = DirectionEvent(1, 21.998, "right", "commands")
        stream = io.StringIO()
        print_direction(event, stream=stream)
        self.assertEqual(stream.getvalue(), "right\n")
        stream = io.StringIO()
        print_direction(event, stream=stream, timestamps=True)
        self.assertEqual(stream.getvalue().strip(), "21.998s right")
        stream = io.StringIO()
        print_direction(event, stream=stream, json_output=True)
        self.assertEqual(json.loads(stream.getvalue()), {
            "type": "direction", "sequence": 1, "time_sec": 21.998,
            "direction": "right", "mode": "commands"})

    def test_main_keeps_diagnostics_out_of_json_stdout(self):
        out, err = io.StringIO(), io.StringIO()
        event = DirectionEvent(1, 2, "up", "commands")
        with patch("playback_directions.Path.is_file", return_value=True), \
                patch("playback_directions.read_json", return_value=self.model), \
                patch("playback_directions.load_recording", return_value=self.recording), \
                patch("playback_directions.prepare_directions", return_value=[event]), \
                redirect_stdout(out), redirect_stderr(err):
            self.assertEqual(main(["--json", "--speed", "0"]), 0)
        self.assertEqual(len(out.getvalue().splitlines()), 1)
        self.assertEqual(json.loads(out.getvalue())["direction"], "up")
        self.assertIn("Playback complete", err.getvalue())

    def test_bad_parameters_and_event_sequences_are_rejected(self):
        for speed in (-1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                replay_directions([], 1, lambda event: None, speed=speed)
        for events in ([DirectionEvent(1, 2, "up", "commands")],
                       [DirectionEvent(1, -1, "up", "commands")],
                       [DirectionEvent(1, 0, "neutral", "commands")]):
            with self.assertRaises(ValueError):
                replay_directions(events, 1, lambda event: None, speed=0)
        with self.assertRaises(ValueError):
            prepare_directions(self.recording, self.model, mode="labels", interval_sec=0)


if __name__ == "__main__":
    unittest.main()
