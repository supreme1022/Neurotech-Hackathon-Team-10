"""Present repeated gaze/blink targets and checkpoint their actual software onset times."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import time
import tkinter as tk

from calibration_session import build_protocol, marker_name, new_session
from eog_pipeline import write_json


class CalibrationGUI:
    def __init__(self, root, output=None, repetitions=3, hold_sec=10,
                 center_sec=6, blink_sec=6, warmup_sec=8, countdown_sec=3,
                 lsl_markers=False, fullscreen=True):
        self.root = root
        self.output = Path(output or datetime.now().strftime("output/session_%Y%m%d_%H%M%S.json"))
        if self.output.exists():
            raise ValueError(f"Session file already exists: {self.output}")
        self.protocol = build_protocol(repetitions, hold_sec, center_sec, blink_sec, warmup_sec)
        if not isinstance(countdown_sec, int) or countdown_sec < 0:
            raise ValueError("Countdown must be a nonnegative integer.")
        self.countdown_sec = countdown_sec
        root.title("EOG calibration")
        root.attributes("-fullscreen", fullscreen)
        root.configure(bg="black")
        self.width = root.winfo_screenwidth() if fullscreen else 1000
        self.height = root.winfo_screenheight() if fullscreen else 700
        self.canvas = tk.Canvas(root, width=self.width, height=self.height,
                                bg="black", highlightthickness=0)
        self.confirmed = tk.BooleanVar(value=False)
        self.checkbox = tk.Checkbutton(
            root, text="I have started the external EEG recording",
            variable=self.confirmed, bg="black", fg="white",
            selectcolor="#333333", activebackground="black", activeforeground="white")
        self.checkbox.pack(side="bottom")
        self.canvas.pack(fill="both", expand=True)
        self.session = new_session(
            self.protocol,
            {"width_px": self.width, "height_px": self.height, "margin_px": 100,
             "fullscreen": fullscreen},
            "lsl" if lsl_markers else "timestamp_log_only")
        self.outlet = None
        self.local_clock = None
        if lsl_markers:
            from pylsl import StreamInfo, StreamOutlet, local_clock
            info = StreamInfo("EOGCalibrationMarkers", "Markers", 1, 0, "string",
                              self.session["session_id"])
            self.outlet = StreamOutlet(info)
            self.local_clock = local_clock
        self.current_step = 0
        self.started_at = None
        self.after_id = None
        self.running = False
        root.bind("<space>", self.start_protocol)
        root.bind("<Escape>", lambda event: self.close())
        root.protocol("WM_DELETE_WINDOW", self.close)
        write_json(self.output, self.session)
        duration = sum(p["duration_sec"] for p in self.protocol)
        self.show_message(
            f"Start EEG recording, then check the box and press SPACE.\n"
            f"Keep your head still and follow each dot.\n"
            f"During BLINK trials, blink once per second while looking at center.\n\n"
            f"Protocol: {duration / 60:.1f} minutes. ESC aborts.\n"
            f"Markers: {'LSL outlet enabled' if lsl_markers else 'timestamp log only'}\n"
            f"Session: {self.output}")

    def show_message(self, text, color="white"):
        self.canvas.delete("all")
        self.canvas.create_text(self.width / 2, self.height / 2, text=text,
                                fill=color, font=("Arial", 20), justify="center",
                                width=self.width - 80)

    def start_protocol(self, event=None):
        if self.running or self.session["status"] == "complete":
            return
        if not self.confirmed.get():
            self.show_message("Start external EEG recording and check the box below.\n"
                              "Then press SPACE.")
            return
        self.running = True
        self.checkbox.configure(state="disabled")
        self.root.unbind("<space>")
        self.session["recording_status"] = "operator confirmed; not electronically verified"
        self.session["status"] = "countdown"
        write_json(self.output, self.session)
        self.countdown(self.countdown_sec)

    def countdown(self, remaining):
        if remaining == 0:
            self.run_step()
            return
        self.show_message(f"Calibration starts in {remaining}...\nKeep recording EEG.")
        self.after_id = self.root.after(1000, self.countdown, remaining - 1)

    def send_marker(self, marker):
        if self.outlet is not None:
            timestamp = self.local_clock()
            self.outlet.push_sample([marker], timestamp=timestamp)
            return timestamp
        return None

    def run_step(self):
        try:
            self._run_step()
        except Exception as exc:
            self.abort(f"Presentation/logging/marker error: {exc}")
            self.show_message(f"Session aborted: {exc}\nPress ESC to exit.", "orange")

    def _run_step(self):
        if self.current_step >= len(self.protocol):
            self.finish()
            return
        trial = self.protocol[self.current_step]
        label = trial["label"]
        cx, cy = self.width / 2, self.height / 2
        positions = {"CENTER": (cx, cy), "BLINK": (cx, cy),
                     "RIGHT": (self.width - 100, cy), "LEFT": (100, cy),
                     "UP": (cx, 100), "DOWN": (cx, self.height - 100)}
        x, y = positions[label]
        self.canvas.delete("all")
        self.canvas.create_oval(x - 18, y - 18, x + 18, y + 18,
                                fill="lime green", outline="white", width=2)
        instruction = ("Blink once per second; keep looking at the dot." if label == "BLINK"
                       else f"Look {label}; keep your head still.")
        # Top-left text stays away from all center/edge targets.
        self.canvas.create_text(
            20, 20, anchor="nw", text=f"{instruction}\n"
            f"Step {self.current_step + 1}/{len(self.protocol)} | "
            f"{trial['duration_sec']:g}s | EEG: operator confirmed",
            fill="white", font=("Arial", 15), width=self.width - 40)
        self.root.update_idletasks()
        now = time.perf_counter()
        if self.started_at is None:
            self.started_at = now
            self.session["started_utc"] = datetime.now(timezone.utc).isoformat()
        onset = now - self.started_at
        if self.session["events"]:
            previous = self.session["events"][-1]
            previous["duration_sec"] = onset - previous["onset_sec"]
        trial_id = str(self.current_step)
        marker = marker_name(self.session["session_id"], trial_id, label)
        event = {
            "trial_id": trial_id, "label": label, "repeat": trial["repeat"],
            "onset_sec": onset, "duration_sec": None, "marker": marker,
            "lsl_timestamp": self.send_marker(marker),
        }
        self.session["events"].append(event)
        self.session["status"] = "running"
        write_json(self.output, self.session)
        self.current_step += 1
        self.after_id = self.root.after(round(trial["duration_sec"] * 1000), self.run_step)

    def finish(self):
        end = time.perf_counter() - self.started_at
        last = self.session["events"][-1]
        last["duration_sec"] = end - last["onset_sec"]
        marker = marker_name(self.session["session_id"], "END", "END")
        self.session["end_marker"] = marker
        self.session["end_lsl_timestamp"] = self.send_marker(marker)
        self.session["duration_sec"] = end
        self.session["finished_utc"] = datetime.now(timezone.utc).isoformat()
        self.session["status"] = "complete"
        write_json(self.output, self.session)
        self.running = False
        self.after_id = None
        self.show_message(f"Calibration protocol complete.\n"
                          f"You can stop external EEG recording.\n"
                          f"Session saved to {self.output}\nPress ESC to exit.", "cyan")

    def abort(self, reason):
        if self.session["status"] in ("complete", "aborted"):
            return
        if self.session["events"] and self.started_at is not None:
            last = self.session["events"][-1]
            last["duration_sec"] = time.perf_counter() - self.started_at - last["onset_sec"]
        self.session["status"] = "aborted"
        self.session["abort_reason"] = reason
        if self.outlet:
            try:
                self.send_marker(marker_name(self.session["session_id"], "ABORT", "ABORT"))
            except Exception:
                pass
        write_json(self.output, self.session)
        self.running = False

    def close(self):
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
        try:
            self.abort("Operator closed the GUI.")
        finally:
            self.root.destroy()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output")
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--hold", type=float, default=10)
    parser.add_argument("--center", type=float, default=6)
    parser.add_argument("--blink", type=float, default=6)
    parser.add_argument("--warmup", type=float, default=8)
    parser.add_argument("--countdown", type=int, default=3)
    parser.add_argument("--lsl-markers", action="store_true")
    parser.add_argument("--windowed", action="store_true")
    args = parser.parse_args(argv)
    root = tk.Tk()
    try:
        CalibrationGUI(root, args.output, args.repetitions, args.hold, args.center,
                       args.blink, args.warmup, args.countdown, args.lsl_markers,
                       not args.windowed)
        root.mainloop()
    except (ValueError, OSError, ImportError, RuntimeError) as exc:
        root.destroy()
        parser.exit(2, f"GUI failed: {exc}\n")


if __name__ == "__main__":
    main()
