# PhoniFide

**Hands-free, voice-free learning, controlled only by where you look.**

PhoniFide is a two-choice learning game for people who cannot easily read, type, tap or
speak. A prompt is spoken out loud, two answers appear far left and far right, and the
learner answers by holding a glance on one of them. The glance is read from an EEG headset
as eye movement (electro-oculography, EOG) on the electrodes beside the eyes, so the only
movement the game needs is the one almost everyone keeps, including people living with ALS.

Built in 30 hours at the **Neurotech @ NC State BCI Hackathon** (November 7-8, 2026) for the
**ANT Neuro track**.

---

## The event

| | |
|---|---|
| **Event** | Neurotech @ NC State BCI Hackathon, organised by the Neurotech @ NC State student club |
| **Dates** | Saturday November 7 (9:00 am - 10:00 pm) and Sunday November 8, 2026 (9:00 am - 2:30 pm) |
| **Venue** | Engineering Building 3, 1840 Entrepreneur Drive, NC State Centennial Campus, Raleigh, NC 27606 |
| **Track** | ANT Neuro: *movement-based neurotech applications*. Build a scalable, everyday-life application that uses EEG-tracked movement as its core input and responds in real time. Judged on the live demo, on the EEG driving the result, on everyday usefulness and creativity, with inclusivity and scalability (NC State Entrepreneurship) as sub-goals. |
| **Hardware** | [ANT Neuro](https://www.ant-neuro.com) eego 24-channel EEG (waveguard net, saline sponge electrodes), streamed live over [Lab Streaming Layer](https://labstreaminglayer.org) from ANT's acquisition laptop to ours. Teams had 30-minute rotations on the headset. |
| **Team 10** | Supreme Constantine (NC State, CSC), Shradha Bhatia (NC State, ECE), Matthew Sanchez (Wake Tech), Sajan Patel (Duke, BME), Miguel Gaido (Durham Tech, CSC) |

<!-- TODO: add the official event / club link here (website, Instagram or Devpost page). -->

---

## The problem

Most learning tools assume you can read, type, tap or speak. The people who need practice
most often cannot do any of those reliably:

- **Dyslexia**: linking sounds to letters is hard (b/d, was/saw, pin/pen).
- **Children learning phonics**: they cannot read the instructions yet.
- **Language learners**, for example immigrants learning English: minimal pairs (ship/sheep, light/right), meaning, spelling.
- **Speech differences**: impediments, facial differences or injuries that make voice interfaces fail.
- **Paralysis or no speech** (for example ALS): left/right becomes yes/no and a way to pick phrases.

## The idea

**Hear it. Look at it. Hold. Done.**

1. **Wear** the EEG headset (and headphones if the room is loud).
2. **Listen**: the game speaks the prompt. *"Which word starts with B?"*
3. **Choices** appear, one far left and one far right. Pictures can be shown too.
4. **Look and hold** your gaze on the answer. The hold time is adjustable. Blinking is fine.
5. **Detect**: the electrodes beside the eyes (F7/F8) read the direction of the glance.
6. **Feedback**: instant, spoken.
7. **Adapt**: every answer is logged with how long the learner hesitated, so missed words can
   come back more often and a teacher or parent gets a report.

Eye movement is the movement. It is the strongest, most reliable signal an EEG cap picks
up, it works in any lighting and at any camera angle, and the same headset can later add
focus and alertness signals that a webcam cannot see.

---

## What is in this repository

```
README.md                 this file
index-2.html              Adaptive reading-lesson web prototype
bridge.py                 EEG -> browser bridge: live engagement, jaw-clench and gaze events for index-2.html
signal-processing branch  EEG/EOG calibration and real-time classification pipeline + tests
```

### `signal-processing` branch: the EOG pipeline

Sajan's standalone pipeline for turning the raw EEG recording into gaze commands, with
unit tests (`python -m unittest discover -s tests -t .`):

- `calibration_GUI.py`: on-screen dot protocol (centre, right, left, up, down, blink), optional LSL markers.
- `calibration.py`: aligns the recording to the protocol, fits per-user thresholds on the
  first repetitions, validates on a held-out final repetition with explicit quality gates
  (recall per state, false activations), writes `output/calibration.json` plus a report and
  diagnostic plot.
- `real_time_classification.py`: causal low-pass filter, 3-second windows, variance gate for
  blinks and transitions, 3-second dwell before a command is emitted. `playback` replays a
  CNT/EDF file; `live` reads an LSL stream.
- Additions made for the real recording: drift-tracking baseline that follows the signal
  only while gaze is centred, horizontal-only calibration, skipping the first (settling)
  repetition, and `estimate_offset.py` to recover the protocol timing from the EEG when the
  GUI log is missing. See that branch's README.

### `index-2.html`: adaptive reading lesson (web)

A single-file web prototype of what the classroom version could look like: dyslexia-friendly
fonts and syllable colouring, read-aloud, two lessons (phonics and comprehension), gaze or
mouse selection with dwell, and an *engagement* meter that switches the lesson to read-aloud
with bigger text when attention drops. It takes EEG engagement and jaw-clench events from
`bridge.py` over a local WebSocket (`ws://localhost:8765`), or runs in simulation mode
without one.

### `bridge.py`: EEG to browser

`python bridge.py --stream "NAME"` reads the live LSL stream and sends the page, four times
a second:

- **engagement**: beta / (theta + alpha) band-power ratio on the frontal and central
  channels, 2-second window, smoothed, scaled against the page's 45-second focus calibration
  (or the first 20 s of the session before that). Relaxing or closing the eyes pulls it down.
- **clench**: a burst of 25-100 Hz muscle activity on the temple electrodes, one event per
  clench. The threshold is automatic (3x the resting level) until the page's jaw calibration
  measures rest and clench levels.
- **gaze**: left / right / centre from F8 - F7 with a drift-tracking baseline, plus a
  `gaze_event` when a new glance is confirmed. The page does not use it yet; the ten lines
  that would let a glance step through the answers are in the `bridge.py` docstring.

`python bridge.py --demo` produces a synthetic signal so the page can be exercised without a
headset. Tested against the page with the synthetic signal and with a simulated 24-channel
LSL headset: the engagement meter followed the signal, the attention-drop adaptation fired
after 20 s of low engagement, and a clench selected the highlighted answer.

---

## What we measured

Our calibration recording (Saturday 5:54 pm, 4.1 minutes, 500 Hz, Sajan wearing the cap,
following the calibration dot: 10-second holds, centre / right / left / up / down / blink,
3 repetitions):

- A left or right glance moves F8 - F7 by about **+190 / -200 uV**. Centre, up, down and
  blinks stay within about +/-50 uV of baseline on that channel pair, so left/right is clean.
- **Up/down is not separable** on this cap: the vertical signal from Fp1/Fp2 is swamped by
  blinks and drift. PhoniFide therefore uses two choices, left and right.
- The electrodes **drift** by about 800 uV over four minutes (and about 20 uV/s during the
  first minute after the cap goes on). A fixed baseline cannot work; the fix is a baseline
  that tracks the signal only while the gaze is centred, and a one-minute wait after the cap
  is placed.
- With those fixes, calibration on repetitions 1-2 and testing on the held-out repetition 3:
  **100% window recall for centre, right and left; 2 of 2 glances detected; 0 false
  activations; about 7 s latency** (3 s window + 3 s dwell). Replaying the whole recording:
  repetitions 2 and 3 gave 4 of 4 glances with 0 false activations. Thresholds came out near
  +136 uV (right) and -145 uV (left).

---

## Running it

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install numpy scipy pylsl websockets

python bridge.py --stream "NAME"      # feed the web prototype from the headset, then open index-2.html
python bridge.py --demo               # same, with a synthetic signal (no headset)
```

Live EEG: the laptop running the bridge and ANT's acquisition laptop must be on the same
network (ANT's router or a phone hotspot), with LSL streaming enabled in the eego software.
`--stream` takes the exact stream name; without it the first stream of type EEG is used.
The calibration and classification pipeline has its own instructions on the
`signal-processing` branch.

---

## Team

| | |
|---|---|
| Supreme Constantine | NC State, Computer Science |
| Shradha Bhatia | NC State, Electrical and Computer Engineering |
| Matthew Sanchez | Wake Tech, Science |
| Sajan Patel | Duke, Biomedical Engineering |
| Miguel Gaido | Durham Tech, Computer Science |
