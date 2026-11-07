"""Optional local LSL transport smoke test; publishes synthetic samples, never hardware EEG."""
from __future__ import annotations

from threading import Event, Thread
import time
import uuid

import numpy as np

from eog_pipeline import CHANNELS
from lsl_input import LSLSource


def main():
    import pylsl

    source_id = "eog-test-" + uuid.uuid4().hex
    info = pylsl.StreamInfo("Synthetic EOG loopback", "EEG", 4, 100,
                           "float32", source_id)
    channels = info.desc().append_child("channels")
    for label in CHANNELS:
        channel = channels.append_child("channel")
        channel.append_child_value("label", label)
        channel.append_child_value("unit", "uV")
    outlet = pylsl.StreamOutlet(info)
    stop = Event()
    errors = []

    def publish():
        try:
            while not stop.is_set():
                outlet.push_sample([1.0, 2.0, 3.0, 4.0])
                stop.wait(0.01)
        except Exception as exc:
            errors.append(exc)

    worker = Thread(target=publish, daemon=True)
    worker.start()
    source = None
    try:
        source = LSLSource(source_id=source_id)
        deadline = time.monotonic() + 8
        observed = 0
        previous = None
        while time.monotonic() < deadline and observed < 20:
            chunk = source.pull()
            if chunk is None:
                continue
            data, timestamps = chunk
            np.testing.assert_allclose(data[:, 0], np.arange(1, 5) * 1e-6)
            if np.any(np.diff(timestamps) <= 0):
                raise AssertionError("LSL sample timestamps are not increasing.")
            if previous is not None and timestamps[0] <= previous:
                raise AssertionError("LSL chunk timestamps overlap.")
            previous = timestamps[-1]
            if abs(source.clock() - timestamps[-1]) > 1:
                raise AssertionError("Clock-corrected EEG is not fresh.")
            observed += len(timestamps)
        if errors:
            raise errors[0]
        if observed < 20:
            raise RuntimeError("Did not receive sufficient loopback samples.")
        print(f"LSL loopback passed: {observed} samples; labels, units, clock and transport verified.")
        print("This does not validate an ANT hardware bridge.")
    finally:
        stop.set()
        worker.join(timeout=2)
        if source is not None:
            source.close()


if __name__ == "__main__":
    main()
