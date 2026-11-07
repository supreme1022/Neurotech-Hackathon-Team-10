"""Optional LSL EEG adapter. Acquisition/ANT hardware must already publish a stream."""
from __future__ import annotations

import numpy as np

from eog_pipeline import CHANNELS, channel_indices


def unit_scale(unit):
    normalized = str(unit).strip().casefold().replace("\u00b5", "u").replace("\u03bc", "u")
    scales = {"v": 1.0, "volt": 1.0, "volts": 1.0,
              "mv": 1e-3, "millivolts": 1e-3,
              "uv": 1e-6, "microvolt": 1e-6, "microvolts": 1e-6}
    if normalized not in scales:
        raise ValueError(f"Unknown EEG amplitude unit {unit!r}; supply --units V, mV or uV "
                         "only after checking the stream's actual scaling.")
    return scales[normalized]


class LSLSource:
    def __init__(self, stream_name=None, source_id=None, mapping=None, units=None):
        import pylsl
        self.pylsl = pylsl
        if bool(stream_name) == bool(source_id):
            raise ValueError("Select exactly one LSL stream name or source ID.")
        prop, value = ("source_id", source_id) if source_id else ("name", stream_name)
        streams = pylsl.resolve_byprop(prop, value, timeout=5.0)
        if len(streams) != 1:
            raise ValueError(f"Expected exactly one LSL stream for {prop}={value!r}; "
                             f"found {len(streams)}.")
        # Clock correction maps remote sample timestamps to this computer's clock.
        # Do not dejitter: acquisition timestamp gaps must remain visible.
        self.inlet = pylsl.StreamInlet(
            streams[0], max_buflen=5, recover=False,
            processing_flags=pylsl.proc_clocksync)
        try:
            info = self.inlet.info(timeout=5.0)
            self.sfreq = float(info.nominal_srate())
            if self.sfreq <= 0:
                raise ValueError("EEG must have a positive nominal sampling frequency.")
            names, channel_units = [], []
            node = info.desc().child("channels").child("channel")
            for _ in range(info.channel_count()):
                names.append(node.child_value("label"))
                channel_units.append(node.child_value("unit"))
                node = node.next_sibling()
            self.indices = channel_indices(names, mapping)
            self.scales = np.asarray([
                unit_scale(units if units is not None else channel_units[i])
                for i in self.indices
            ])
            self.metadata = {
                "mode": "live_lsl", "stream_name": info.name(),
                "source_id": info.source_id(), "sfreq_hz": self.sfreq,
                "channels": dict(zip(CHANNELS, [names[i] for i in self.indices])),
                "input_units": units or [channel_units[i] for i in self.indices],
                "clock": "LSL local clock via proc_clocksync",
            }
        except Exception:
            self.close()
            raise

    def pull(self, timeout=0.2):
        samples, timestamps = self.inlet.pull_chunk(
            timeout=timeout, max_samples=max(1, round(self.sfreq * 0.2)))
        if not timestamps:
            return None
        matrix = np.asarray(samples, dtype=float)
        if matrix.ndim != 2 or matrix.shape[0] != len(timestamps):
            raise ValueError("LSL returned malformed EEG samples.")
        return (matrix[:, self.indices].T * self.scales[:, None],
                np.asarray(timestamps, dtype=float))

    def clock(self):
        return self.pylsl.local_clock()

    def close(self):
        if getattr(self, "inlet", None) is not None:
            self.inlet.close_stream()
