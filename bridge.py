"""EEG -> browser bridge for index-2.html (the adaptive reading-lesson prototype).

The web page opens ws://localhost:8765 and expects, several times a second:

    {"engagement": 0.0-1.0, "clench": true|false,
     "calibrated": {"focus": bool, "jaw": bool}, "events": ["text", ...]}

and it sends calibration requests when its buttons are pressed:

    {"cmd": "collect", "label": "focus" | "rest_jaw" | "clench", "seconds": N}

This bridge reads a live EEG stream over LSL (ANT eego through the eego software, or any
other LSL EEG stream) and fills those fields from the signal:

  engagement   beta / (theta + alpha) band-power ratio on the frontal and central channels,
               2-second window, smoothed, mapped to 0-1 against the "focus" calibration (or,
               before that, the first 20 s of the session). Relaxing or closing the eyes
               raises alpha and pulls it down; concentrating pushes it up. The page switches
               the lesson to read-aloud with bigger text when it stays below 0.30.
  clench       a burst of muscle activity (25-100 Hz, 60 Hz hum excluded) on the temple
               electrodes (T7, T8, F7, F8, ...) well above the resting level. One event per
               clench, 1.5 s refractory period. Threshold is automatic (3x the resting level)
               until the page's jaw calibration measures rest and clench levels.
  gaze         extra: LEFT / RIGHT / CENTER from the horizontal eye signal F8 - F7 with a
               drift-tracking baseline, plus "gaze_event" on the tick a new glance is confirmed
               (session 2 glances were about +/-190 uV; the default threshold is 100 uV). The
               page ignores these fields today; see "Using gaze in the page" below.

Run:
    python bridge.py                     # first LSL stream of type EEG
    python bridge.py --stream "NAME"     # exact stream name (several headsets in the room)
    python bridge.py --demo              # no headset: a synthetic signal, to exercise the page
Then open index-2.html, untick "Simulation mode" and press "Start lesson".
(Port 8765 is also used by the PhoniFide game's chat mode; do not run both at once.)

Using gaze in the page (optional, about ten lines in index-2.html): add
    <option value="eeg">EEG glance</option>
to the #gazeSrc select, and inside ws.onmessage:
    if (d.gaze_event && $('#gazeSrc').value === 'eeg') stepChoice(d.gaze_event === 'RIGHT' ? 1 : -1);
where stepChoice(k) moves the .hover highlight to the next or previous .choice button.
A clench (or dwell) then selects the highlighted answer, so the lesson runs on eyes and jaw.

Requires: numpy, scipy, pylsl, websockets (pip install numpy scipy pylsl websockets).
"""
from __future__ import annotations

import argparse
import asyncio
import collections
import csv
import json
import math
import threading
import time

import numpy as np
from scipy.signal import welch

EYE_PAIRS = [("F8", "F7"), ("F10", "F9")]
EMG_CHANNELS = ("T7", "T8", "F7", "F8", "F9", "F10", "T9", "T10", "FT7", "FT8", "TP7", "TP8")
ENGAGEMENT_CHANNELS = ("F3", "Fz", "F4", "FC1", "FC2", "FC5", "FC6", "C3", "Cz", "C4",
                       "CP1", "CP2", "AFz", "FCz", "CPz", "Pz")
EMG_BANDS = ((25, 55), (65, 100))  # skip 55-65 Hz so mains hum does not count as muscle


def sigmoid(x):
    return 1.0 / (1.0 + math.exp(-x))


class Features:
    """Latest signal features, handed from the EEG thread to the asyncio loop."""

    def __init__(self):
        self.lock = threading.Lock()
        self.h_uv = None
        self.emg_uv = None
        self.ratio = None
        self.status = "starting"
        self.updated = 0.0

    def set(self, **values):
        with self.lock:
            for key, value in values.items():
                setattr(self, key, value)
            if any(k in values for k in ("h_uv", "emg_uv", "ratio")):
                self.updated = time.monotonic()

    def get(self):
        with self.lock:
            stale = time.monotonic() - self.updated > 2.0
            return {"h_uv": None if stale else self.h_uv,
                    "emg_uv": None if stale else self.emg_uv,
                    "ratio": None if stale else self.ratio,
                    "status": self.status if not stale else f"{self.status} (no fresh samples)"}


def band_power(f, p, lo, hi, chans):
    """Mean over channels of the power in [lo, hi) Hz, in uV^2."""
    mask = (f >= lo) & (f < hi)
    if not mask.any() or not chans:
        return 0.0
    df = f[1] - f[0]
    return float(np.mean(p[np.ix_(chans, np.flatnonzero(mask))].sum(axis=1) * df))


def eeg_thread(features, stream_name, stop):
    import pylsl
    features.set(status="looking for EEG stream...")
    found = (pylsl.resolve_byprop("name", stream_name, timeout=15) if stream_name
             else pylsl.resolve_byprop("type", "EEG", timeout=15))
    if not found:
        features.set(status="no EEG stream found (same Wi-Fi as the ANT laptop? LSL streaming on?)")
        return
    inlet = pylsl.StreamInlet(found[0], max_buflen=30,
                              processing_flags=pylsl.proc_clocksync | pylsl.proc_dejitter)
    info = inlet.info(timeout=5)
    fs = float(info.nominal_srate() or 500)
    labels, node = [], info.desc().child("channels").child("channel")
    for i in range(info.channel_count()):
        labels.append(node.child_value("label") or f"ch{i + 1}")
        node = node.next_sibling()
    low = [label.lower() for label in labels]

    def indices(names):
        return [low.index(n.lower()) for n in names if n.lower() in low]

    pair = next(((low.index(a.lower()), low.index(b.lower()), f"{a}-{b}")
                 for a, b in EYE_PAIRS if a.lower() in low and b.lower() in low), None)
    emg = indices(EMG_CHANNELS) or list(range(len(labels)))
    eng = indices(ENGAGEMENT_CHANNELS) or [i for i in range(len(labels)) if i not in emg] or emg
    print(f"Connected to '{info.name()}' from {info.hostname()}: {len(labels)} channels @ {fs:g} Hz")
    print(f"  eye pair:            {pair[2] if pair else 'none (no F7/F8 or F9/F10): gaze disabled'}")
    print(f"  clench channels:     {[labels[i] for i in emg]}")
    print(f"  engagement channels: {[labels[i] for i in eng]}")
    features.set(status=f"'{info.name()}' {pair[2] if pair else ''} @ {fs:g} Hz")

    window = collections.deque(maxlen=int(fs * 2))
    eye_n, emg_n = max(1, int(fs * 0.15)), max(8, int(fs * 0.5))
    scale, last = None, 0.0
    while not stop.is_set():
        chunk, stamps = inlet.pull_chunk(timeout=0.1, max_samples=4096)
        if not stamps:
            continue
        block = np.asarray(chunk, dtype=float)
        if scale is None:  # streams in volts need converting to microvolts
            scale = 1e6 if np.nanmedian(np.abs(block)) < 1.0 else 1.0
        window.extend(block * scale)
        now = time.monotonic()
        if now - last < 0.2 or len(window) < fs:
            continue
        last = now
        data = np.asarray(window)  # samples x channels, uV
        h = None
        if pair:
            recent = data[-eye_n:]
            h = float(np.median(recent[:, pair[0]] - recent[:, pair[1]]))
        centred = data - data.mean(axis=0)
        f, p = welch(centred.T, fs=fs, nperseg=min(len(centred), int(fs)))
        theta = band_power(f, p, 4, 8, eng)
        alpha = band_power(f, p, 8, 13, eng)
        beta = band_power(f, p, 13, 30, eng)
        ratio = beta / (theta + alpha) if theta + alpha > 0 else None
        tail = centred[-emg_n:]
        f2, p2 = welch(tail.T, fs=fs, nperseg=min(len(tail), max(8, int(fs * 0.25))))
        power = sum(band_power(f2, p2, lo, min(hi, fs / 2 - 1), emg)
                    for lo, hi in EMG_BANDS if lo < fs / 2 - 1)
        features.set(h_uv=h, emg_uv=math.sqrt(power), ratio=ratio)
    inlet.close_stream()


def demo_thread(features, stop):
    """Synthetic features so the page can be exercised without a headset."""
    rng = np.random.default_rng(0)
    features.set(status="DEMO signal, no headset")
    t0 = time.monotonic()
    while not stop.is_set():
        t = time.monotonic() - t0
        phase = t % 90
        focused = not (40 < phase < 65)  # a 25-second attention dip every 90 seconds
        ratio = (0.25 if focused else 0.07) * math.exp(rng.normal(0, 0.15))
        emg = 4.0 + abs(rng.normal(0, 0.3)) + (40.0 if (t % 12) < 0.6 else 0.0)  # clench every 12 s
        k = int(t // 7)
        glance = (200 if k % 2 else -200) if (t % 7) < 1.5 else 0  # alternating glances every 7 s
        h = 60 * math.sin(t / 30) + glance + rng.normal(0, 5)  # plus slow electrode drift
        features.set(h_uv=h, emg_uv=emg, ratio=ratio)
        time.sleep(0.2)


class Bridge:
    """Turns raw features into the page's engagement / clench / gaze messages."""

    def __init__(self, args):
        self.tick = args.tick
        self.glance_uv = args.glance_uv
        self.flip = args.flip
        self.started = time.monotonic()
        self.calibrated = {"focus": False, "jaw": False}
        self.collect = None
        self.events = []
        self.jaw = {}
        # engagement
        self.log_ratio = None
        self.ref_log = None
        self.warm = []
        # clench
        self.rest_history = collections.deque(maxlen=int(10 / self.tick))
        self.emg_threshold = None
        self.clench_run = 0
        self.last_clench = -10.0
        # gaze
        self.base = None
        self.direction = "CENTER"
        self.direction_since = self.started
        self.gaze = "CENTER"
        self.writer = None
        if args.log:
            handle = open(args.log, "w", newline="", encoding="utf-8")
            self.writer = csv.writer(handle)
            self.writer.writerow(["t_sec", "engagement", "ratio", "emg_uv", "clench", "h_uv", "gaze", "status"])

    # ---- commands from the page -------------------------------------------------
    def command(self, obj):
        if obj.get("cmd") != "collect":
            self.events.append(f"ignored command {obj!r}")
            return
        label, seconds = obj.get("label"), float(obj.get("seconds", 10))
        if label not in ("focus", "rest_jaw", "clench"):
            self.events.append(f"unknown collect label {label!r}")
            return
        self.collect = {"label": label, "until": time.monotonic() + seconds, "values": []}
        self.events.append(f"collecting '{label}' for {seconds:g} s")

    def finish_collect(self):
        label, values = self.collect["label"], np.asarray(self.collect["values"], dtype=float)
        self.collect = None
        values = values[np.isfinite(values)]
        if len(values) < 4:
            self.events.append(f"'{label}' calibration got no signal; nothing changed")
            return
        if label == "focus":
            self.ref_log = float(np.median(values))
            self.calibrated["focus"] = True
            self.events.append(f"focus calibrated: reference ratio {math.exp(self.ref_log):.2f}")
            return
        self.jaw[label] = values
        if "rest_jaw" in self.jaw and "clench" in self.jaw:
            rest_high = float(np.percentile(self.jaw["rest_jaw"], 95))
            clench_level = float(np.percentile(self.jaw["clench"], 75))
            if clench_level > 1.5 * rest_high:
                self.emg_threshold = math.sqrt(rest_high * clench_level)
                self.calibrated["jaw"] = True
                self.events.append(f"jaw calibrated: rest {rest_high:.1f} uV, clench {clench_level:.1f} uV, "
                                   f"threshold {self.emg_threshold:.1f} uV")
            else:
                self.events.append(f"clench ({clench_level:.1f} uV) not clearly above rest ({rest_high:.1f} uV); "
                                   "keeping the automatic threshold. Clench harder and retry.")

    # ---- one tick ------------------------------------------------------------------
    def step(self, f):
        now = time.monotonic()
        events, self.events = self.events, []
        ratio, emg, h = f["ratio"], f["emg_uv"], f["h_uv"]

        # engagement: smoothed log band ratio against a reference
        if ratio:
            lr = math.log(ratio)
            self.log_ratio = lr if self.log_ratio is None else self.log_ratio + (self.tick / 3.0) * (lr - self.log_ratio)
            if self.ref_log is None:
                self.warm.append(lr)
                if now - self.started > 20:
                    self.ref_log = float(np.median(self.warm))
                    events.append(f"engagement reference set from the first 20 s (ratio {math.exp(self.ref_log):.2f}); "
                                  "use 'Calibrate focus' for a proper one")
        if self.ref_log is None or self.log_ratio is None:
            engagement = 0.5
        else:
            engagement = min(0.98, max(0.02, sigmoid(0.62 + 1.565 * (self.log_ratio - self.ref_log))))

        # clench: EMG burst above threshold for two ticks, one event per burst
        fire = False
        threshold = self.emg_threshold
        if emg is not None:
            if threshold is None:
                if self.rest_history:
                    rest = float(np.median(self.rest_history))
                    threshold = max(3.0 * rest, rest + 3.0)
                    if emg < 2.5 * rest:
                        self.rest_history.append(emg)
                else:
                    self.rest_history.append(emg)
                    threshold = float("inf")
            self.clench_run = self.clench_run + 1 if emg > threshold else 0
            if self.clench_run == 2 and now - self.last_clench > 1.5:
                fire = True
                self.last_clench = now
                events.append(f"clench ({emg:.0f} uV, threshold {threshold:.0f} uV)")

        # gaze: drift-tracking baseline, glance = step beyond the threshold held for 0.5 s
        gaze_event = None
        if h is not None:
            if self.flip:
                h = -h
            if self.base is None:
                self.base = h
            delta = h - self.base
            if abs(delta) < 0.6 * self.glance_uv:
                self.base += (self.tick / 2.0) * delta  # follow slow drift only while centred
            direction = "RIGHT" if delta > self.glance_uv else "LEFT" if delta < -self.glance_uv else "CENTER"
            if direction != self.direction:
                self.direction, self.direction_since = direction, now
            held = now - self.direction_since
            if direction != "CENTER" and held >= 0.5 and self.gaze != direction:
                self.gaze = gaze_event = direction
                events.append(f"glance {direction} ({delta:+.0f} uV)")
            elif direction == "CENTER" and held >= 0.3:
                self.gaze = "CENTER"
            if direction != "CENTER" and held > 8:
                self.base = h  # nobody holds a glance that long: the electrodes drifted
                events.append("re-centred: a 'glance' held for 8 s is drift")

        # calibration collection
        if self.collect:
            value = {"focus": math.log(ratio) if ratio else None, "rest_jaw": emg, "clench": emg}[self.collect["label"]]
            if value is not None:
                self.collect["values"].append(value)
            if now >= self.collect["until"]:
                self.finish_collect()
                events.extend(self.events)
                self.events = []

        t = round(now - self.started, 2)
        if self.writer:
            self.writer.writerow([t, round(engagement, 3), None if ratio is None else round(ratio, 4),
                                  None if emg is None else round(emg, 2), int(fire),
                                  None if h is None else round(h, 1), self.gaze, f["status"]])
        return {
            "engagement": round(engagement, 3), "clench": fire,
            "calibrated": dict(self.calibrated), "events": events,
            "gaze": self.gaze if h is not None else None, "gaze_event": gaze_event,
            "signal": {"h_uv": None if h is None else round(h, 1),
                       "emg_uv": None if emg is None else round(emg, 2),
                       "ratio": None if ratio is None else round(ratio, 4)},
            "status": f["status"], "t": t,
        }


async def run(args):
    import websockets
    features, stop, bridge = Features(), threading.Event(), Bridge(args)
    if args.demo:
        worker = threading.Thread(target=demo_thread, args=(features, stop), daemon=True)
    else:
        worker = threading.Thread(target=eeg_thread, args=(features, args.stream, stop), daemon=True)
    worker.start()
    clients = set()

    async def handler(connection):
        clients.add(connection)
        print(f"page connected ({len(clients)} open)")
        try:
            async for raw in connection:
                try:
                    bridge.command(json.loads(raw))
                except (ValueError, TypeError) as exc:
                    print("bad command from page:", exc)
        finally:
            clients.discard(connection)
            print("page disconnected")

    async with websockets.serve(handler, args.host, args.port):
        print(f"Bridge listening on ws://{args.host}:{args.port}. Open index-2.html, untick "
              "'Simulation mode', press 'Start lesson'. Ctrl+C to stop.")
        last_status = None
        try:
            while True:
                f = features.get()
                if f["status"] != last_status:
                    print("EEG:", f["status"])
                    last_status = f["status"]
                message = bridge.step(f)
                for event in message["events"]:
                    print(f"[{message['t']:7.1f} s] {event}")
                if clients:
                    websockets.broadcast(clients, json.dumps(message))
                await asyncio.sleep(args.tick)
        finally:
            stop.set()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stream", help="exact LSL stream name (default: first stream of type EEG)")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=8765, help="the page connects to ws://localhost:8765")
    parser.add_argument("--demo", action="store_true", help="synthetic signal instead of LSL")
    parser.add_argument("--tick", type=float, default=0.25, help="seconds between messages to the page")
    parser.add_argument("--glance-uv", type=float, default=100.0, help="F8-F7 step that counts as a glance")
    parser.add_argument("--flip", action="store_true", help="swap LEFT/RIGHT if the polarity is reversed")
    parser.add_argument("--log", help="CSV of every tick (evidence for the write-up)")
    args = parser.parse_args(argv)
    try:
        asyncio.run(run(args))
    except KeyboardInterrupt:
        print("stopped")


if __name__ == "__main__":
    main()
