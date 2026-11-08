# PhoniFide

**Hands-free, voice-free learning, controlled only by where you look.**

PhoniFide is a two-choice learning and communication system controlled by eye movement alone.
A prompt is spoken out loud, two answers appear far left and far right, and the learner
answers by holding a glance on one of them. The glance is read from an EEG headset as eye
movement (electro-oculography, EOG) on the electrodes beside the eyes, so it needs no hands,
no voice, no reading and no camera. That opens it to the people most learning tools leave
out: children learning phonics who cannot read the instructions yet; learners with dyslexia;
immigrants learning a new language one word pair at a time; people
with speech differences or facial injuries that defeat voice interfaces; and people living
with paralysis, ALS or locked-in syndrome, for whom the same left/right glance becomes yes/no,
a way to pick phrases, and a way to keep learning. Every answer is logged with how long the
learner hesitated, so a teacher, parent or therapist sees which words keep failing, and the
same headset can add attention and jaw-clench signals that no camera can see.

Built in 30 hours at the **Neurotech @ NC State BCI Hackathon** (November 7-8, 2026) for the
**ANT Neuro track**.


**Sections**

- [The idea](#the-idea) and [What is new here](#what-is-new-here)
- [Who it is for, and how it gets into the world](#who-it-is-for-and-how-it-gets-into-the-world)
- [The hard parts](#the-hard-parts)
- [Evidence](#evidence), [Limitations](#limitations), [Running it](#running-it)
- [Movement: eyes still versus eyes moving](#movement-eyes-still-versus-eyes-moving)
- [Accommodations](#accommodations)

---

## The event

| | |
|---|---|
| **Event** | Neurotech @ NC State BCI Hackathon, organised by the Neurotech @ NC State student club |
| **Dates** | Saturday November 7 (9:00 am - 10:00 pm) and Sunday November 8, 2026 (9:00 am - 2:30 pm) |
| **Venue** | Engineering Building 3, 1840 Entrepreneur Drive, NC State Centennial Campus, Raleigh, NC 27606 |
| **Track** | ANT Neuro: *movement-based neurotech applications*. Build a scalable, everyday-life application that uses EEG-tracked movement as its core input and responds in real time. Judged on creativity, practicality, technical difficulty, execution, movement integration and inclusivity. |
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

### What is new here

- **The glance is the answer, not a cursor.** Most eye-based interfaces steer a pointer, which
  demands precision the eye signal does not have. PhoniFide asks a question and reads one
  committed glance, so the limits of EOG (coarse direction, slow drift) stop mattering.
- **Two choices by design.** Left/right is the one axis an EEG cap reads cleanly, so the
  content is built as pairs: b/d, was/saw, ship/sheep, yes/no. That matches how phonics and
  minimal-pair practice already work.
- **Built to survive real electrodes.** Instead of assuming a clean signal, the detector
  re-centres before every question and tracks drift while the eyes are still, with a
  pass/fail calibration so a bad setup is reported instead of silently misread.

---

## Movement: eyes still versus eyes moving

The movement this project uses is eye movement, and it is central: nothing in the game
happens without it. Everything below was measured on the recording in this repository
(`recording.cnt` on the `signal-processing` branch: 4.1 minutes, 500 Hz, one team member
following a calibration dot through centre / right / left / up / down / blink, 10-second
holds, 3 repetitions).

| State of the eyes | F8 - F7 | What the detector does |
|---|---|---|
| **Still**, on the centre dot | stays within about +/-50 uV of baseline | nothing; the baseline keeps tracking |
| **Moving**: glance right / left and hold | about **+190 / -200 uV** | a command after 3 s of dwell |
| Blink | a brief pulse, largely cancelled on this bipolar pair | masked by the median window and the variance gate |
| Up / down | buried in blinks and drift on Fp1/Fp2 | not used |

- **Still versus moving test:** calibrating on repetitions 1-2 and testing on the held-out
  repetition 3, every still (centre) window was classified as still (143 of 143) and every
  glance window as its direction (47 of 47 right, 47 of 47 left), with **0 false activations**.
  Replaying repetitions 2 and 3 gave 4 of 4 glances and 0 false activations; the settling
  first repetition is reported under *Where the numbers come from*.
- **Artifact checks:**
  - *Blinks*, the largest artifact on a frontal EEG: rejected by a 3-second median window and
    a variance gate in the causal detector; masked as pulses before baseline estimation in the
    offline recovery mode.
  - *Electrode drift*: about 800 uV over four minutes, and about 20 uV/s during the first
    minute after the cap goes on. Handled by a baseline that follows the signal only while the
    gaze is centred (the causal detector and `bridge.py`) or by a 10-second Gaussian baseline
    estimate (offline recovery mode), plus a one-minute wait after the cap is placed.
  - *Muscle (EMG)*: the jaw-clench detector in `bridge.py` measures 25-55 Hz and 65-100 Hz,
    straddling the 60 Hz mains line so line noise cannot trigger it.
- **Not yet tested:** walking and head turns. See [Limitations](#limitations).

---

## Who it is for, and how it gets into the world

**User value.** A learner who cannot read, speak or use their hands gets a way to practise
that gives instant feedback, and a teacher or parent gets a per-learner list of the words
that keep failing, with hesitation times. For a non-speaking user the same mechanism is a
yes/no channel. The web app gives each role its own door (student code, parent, educator)
and a progress dashboard with lessons finished and practice accuracy.

**Cost and setup.** One EEG headset streaming over LSL, one laptop, saline for the sponges.
Putting the cap on takes about five minutes; the signal needs about one minute to settle;
calibration is 40 seconds of following a dot. Nothing else is needed, and nothing needs the
internet.

**Deployment path.**

1. *Now:* clinics and labs that already own a research EEG system, such as ALS clinics and
   university reading clinics, running the game from a laptop.
2. *Next:* cheaper headbands, provided they put an electrode beside each eye. The horizontal
   eye signal lives at F7/F8; a forehead-only band cannot read it.
3. *At home and in classrooms:* the game logic does not care where the glance comes from, so
   a webcam can drive the same two-choice interface where no headset exists. The headset
   remains the version that also sees attention and clench.

**Reliability.** Per-user calibration with explicit pass/fail quality gates (a bad setup is
reported, not silently misread), a re-centre on the dot before every question, an adjustable
hold time, and an impedance check before each session.

**Safety.** EEG only records; nothing is sent into the body. The electrodes are saline
sponges. Sessions are short by design because every answer needs a deliberate hold.

**Privacy.** All signal processing runs on the laptop. `bridge.py` talks to the web page over
a local WebSocket on the same machine, no raw EEG leaves the device, no video is recorded,
and the logs hold only answers and hesitation times. No account is needed.

**Known risks** (electrode contact through thick hair, head movement during a hold, fatigue)
are listed under [Limitations](#limitations) with what we do about each.

---

## Accommodations

| Barrier | Accommodation | Where it is |
|---|---|---|
| Cannot read yet | Prompts are spoken; pictures can sit beside words | game design; read-aloud in `index-2.html`; audio prompts setting in the web app onboarding |
| Dyslexia | Minimal pairs (b/d, was/saw); dyslexia-friendly font, syllable colouring, read-aloud | `index-2.html` |
| Attention drifts | Engagement meter switches the lesson to read-aloud with bigger text after 20 s of low engagement | `bridge.py` + `index-2.html` |
| Cannot speak | No voice needed; left/right doubles as yes/no | design |
| Cannot use hands | No touch; glance and hold, with an optional jaw-clench confirm | design; `bridge.py` |
| Limited motor control, fatigue | Hold time adjustable; blinks do not count; short sessions | detector parameters; hold-time and sensitivity settings in the web app device setup |
| Different first language | Spoken prompts can be in any language; pairs built for English learners (ship/sheep, light/right) | content packs |
| Resources | Runs offline on one laptop; open source; a webcam path where no headset exists | design |

**Evidence so far.** The separability numbers above show the input works for a seated adult
wearer. The attention-drop adaptation and the clench-to-select path were exercised end to end
with a simulated headset. **Not yet done:** testing with the intended users.

**Test plan.** (1) Five learners with a reading specialist: accuracy, hesitation and the
hold time each learner prefers. (2) A session at an ALS clinic with a speech-language
pathologist, using the yes/no mode. (3) A still-versus-walking recording with the same dot
protocol, to measure how much movement the detector tolerates.

---

## What is in this repository

```
README.md                 this file
@latest/                  PhoniFide web app: landing page, onboarding (learning profile, device setup), lesson UI
                          (React + TypeScript + Vite + Tailwind)
index-2.html              adaptive reading-lesson web prototype
bridge.py                 EEG -> browser bridge: live engagement, jaw-clench and gaze events for index-2.html
signal-processing branch  EOG calibration + classification pipeline, tests, docs and the recordings
drift-tracking branch     the same pipeline + causal drift-tracking baseline, estimate_offset.py, 28 tests,
                          and results/sesh2/ (the saved runs behind the numbers in this README)
```

```
ANT eego 24-ch  --Wi-Fi / LSL-->  bridge.py  --ws://localhost:8765-->  index-2.html
                                  engagement, clench, gaze               lesson adapts, clench selects

@latest/ web app (onboarding, lesson UI, dashboard)   <-- next step: the same bridge.py events

recording.cnt  -->  calibration.py  -->  calibration.json  -->  real_time_classification.py
                    thresholds + quality gates                   playback_directions.py  -->  left / right
```

### `@latest/`: the PhoniFide web app

The product front end, built with React 19, TypeScript, Vite and Tailwind. Routes:

- `/` landing page: audio-guided lessons, adaptive learning, progress tracking, the learning
  gap it addresses, and a section for educators.
- `/get-started`: three ways in: student (enter a student code), parent, educator.
- `/onboarding/learning-profile`: learner name and goals (letter sounds, word reading,
  listening and focus, reading confidence).
- `/onboarding/device-setup`: headset connection, signal quality, a calibration preview (look
  left, look right, hold steady), sensitivity and hold-time settings, audio prompts on or off.
- `/onboarding/ready` and `/lesson`: a phonics lesson with two picture choices, "look left or
  right, then hold steady", and correct / try-again feedback.
- A student dashboard (lessons finished, practice accuracy, recommended practice) and a
  lesson-session view with an eye-tracking indicator are built and not yet routed.

The pages are a UI prototype: choices are selected by click, the headset panels show
placeholder values, and the lesson page can play a scripted timeline (`timings.csv`, the
direction schedule of our recorded session) for demo videos. That playback is a script, not
live EEG, and is labelled as such wherever it is shown. Wiring them to the `bridge.py` gaze and engagement events, the way
`index-2.html` already is, is the next step; the event format is already defined.

```powershell
cd @latest
npm install
npm run dev          # http://localhost:5173
```

### `signal-processing` branch: the EOG pipeline

A standalone pipeline that turns the raw EEG recording into gaze commands:

- `calibration_GUI.py`: on-screen dot protocol (centre, right, left, up, down, blink), with
  optional LSL markers.
- `calibration.py`: aligns the recording to the protocol, fits per-user thresholds on the
  first repetitions, validates on a held-out final repetition with explicit quality gates
  (recall per state, false activations), and writes `calibration.json` plus a report and a
  diagnostic plot. Its `--offline-drift --command-calibration` recovery mode handles drifting
  recordings with blinks: blink pulses are masked, a 10-second Gaussian baseline is removed,
  features are one-second medians and scaled MADs, and acceptance requires zero false
  activations in the held-out repetition. That mode uses future samples, so it is for saved
  files only.
- `real_time_classification.py`: causal 5 Hz low-pass, 3-second windows, variance gate for
  blinks and transitions, 3-second dwell before a command is emitted. `playback` replays a
  CNT/EDF file; `live` reads an LSL stream.
- `playback_directions.py`: replays `recording.cnt` and prints `left` / `right` as commands
  are confirmed, with `--json` events ready for a front end.
- `lsl_input.py`, `calibration_session.py`, `docs/advanced.md`, and `tests/` (44 unit tests).
- The recordings: `recording.cnt` (the 4.1-minute calibration session used throughout this
  README) and the shorter first session.

### `drift-tracking` branch: the variant behind the numbers

The pipeline as of its 9f8e111 commit plus the causal additions used for the results in this
README: a baseline that follows the signal only while the gaze is at centre
(`--baseline-track`, with `--baseline-rescue` for runaway holds), horizontal-only calibration
(`--directions RIGHT,LEFT`), skipping the settling repetition (`--skip-repeats 1`), and
`estimate_offset.py`, which recovers the dot-schedule timing from the EEG when no log exists.
It carries `recording.cnt`, 28 unit tests (`tests/test_drift.py` covers the additions) and
`results/sesh2/` with the calibration JSON and report, diagnostic plots, playback log and
prediction summary those commands produced. Its README gives the exact three commands.

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
headset.

---

## The hard parts

1. **Drift versus a DC signal.** A glance-and-hold is a step that stays up for seconds, and the
   electrodes drift by 800 uV over four minutes, four times the size of the glance. The usual
   fix, a high-pass filter, destroys exactly the signal we need: it turns a hold into a
   decaying pulse and the dwell logic never confirms. Two answers live in this repository: a
   causal baseline that follows the signal only while the gaze is centred (used live in
   `bridge.py`, with a re-centre before every question), and an offline Gaussian baseline
   estimate for analysing saved recordings.
2. **Blinks.** The largest artifact on frontal EEG, one to two seconds long. On the bipolar
   pair F8 - F7 most of a blink cancels; what remains is caught by a median window and a
   variance gate, or masked as pulses before the baseline is estimated offline.
3. **The vertical axis does not exist on this cap.** Up/down on Fp1/Fp2 is swamped by blinks
   and drift, so the design committed to two choices instead of four.
4. **Lost timing.** The recording had no marker stream and the dot schedule's log was lost.
   The protocol timing was recovered from the EEG itself by matching F8 - F7 to the dot
   schedule (offset 4.52 s), and calibration is checked at both ends of the timing bound.
5. **Validation that cannot flatter itself.** Thresholds are fitted on repetitions 1-2 and
   judged on the held-out repetition 3, with per-state recall gates and zero false
   activations required. The first repetition, recorded while the electrodes were still
   settling, is skipped for fitting.
6. **Thresholds, not a black box.** With four minutes of data from one wearer, a trained
   classifier would memorise the recording. Per-user thresholds in microvolts calibrate in
   40 seconds, need no training set, and fail in ways a teacher can understand.
7. **Three pieces from three laptops.** The pipeline (Python), the lesson page (HTML) and the
   headset (ANT's acquisition laptop) had to meet: eego to LSL over Wi-Fi, Welch band powers
   in Python, JSON over a WebSocket to the browser, with the EMG bands chosen to straddle the
   60 Hz mains line, and the networking (hotspot, firewall rules) to make two laptops talk.

---

## Evidence

### What we measured

Our calibration recording (Saturday 5:54 pm, 4.1 minutes, 500 Hz, one team member wearing the
cap, following the calibration dot: 10-second holds, centre / right / left / up / down / blink,
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
  **100% window recall for centre, right and left (143 / 47 / 47 windows); 2 of 2 glances
  detected; 0 false activations; about 7 s latency** (3 s window + 3 s dwell). Replaying the
  whole recording: repetitions 2 and 3 gave 4 of 4 glances with 0 false activations; the
  settling first repetition is reported under *Where the numbers come from*.
  Thresholds came out near +136 uV (right) and -145 uV (left).

From the saved calibration report:

```json
"quality": {"passed": true, "minimum_required_recall": 0.8,
            "per_class": {"CENTER": {"windows": 143, "recall": 1.0},
                          "RIGHT":  {"windows": 47,  "recall": 1.0},
                          "LEFT":   {"windows": 47,  "recall": 1.0}},
            "held_out_trial_accuracy": 1.0},
"directions": {"RIGHT": {"threshold_uv": 136.0}, "LEFT": {"threshold_uv": 145.0}},
"session": {"alignment": {"offset_sec": 4.52}, "held_out_repeat": 2, "skipped_repeats": 1}
```

### Testing

- `signal-processing` branch: **44 unit tests** (synthetic fixtures, offline recovery mode,
  playback), run with `python -m unittest discover -s tests -t .`.
- `drift-tracking` branch: **28 unit tests**, including `tests/test_drift.py` for the baseline
  tracker, the rescue, the direction subset and repetition skipping.
- `bridge.py`: exercised with its synthetic `--demo` signal, with a simulated 24-channel LSL
  headset, and against the real page in a browser: the engagement meter followed the signal,
  the attention-drop adaptation fired after 20 s of low engagement, and a clench selected the
  highlighted answer.
- The live headset test of the full chain is the remaining step; see [Limitations](#limitations).

### Where the numbers come from

The gaze numbers above were produced on the `drift-tracking` branch: `estimate_offset.py`,
then `calibration.py` with `--baseline-track 2 --baseline-rescue 15 --skip-repeats 1
--directions RIGHT,LEFT`, then `real_time_classification.py playback`, all on `recording.cnt`.
The saved outputs are on that branch under `results/sesh2/`, so the figures can be checked
without re-running anything.

The full replay is reported in full: 7 activations for 6 glances. Repetitions 2 and 3 gave
4 of 4 glances with 0 false activations. Repetition 1, recorded during the first settling
minute, missed its right glance and produced 2 false left calls, which is why the one-minute
wait after the cap goes on is part of the protocol.

The `signal-processing` branch ships a separate offline recovery mode for the same recording;
its report lists recalls, false activations and timing sensitivity rather than hiding them,
and its own documentation says its within-recording results are exploratory rather than
blind validation. We agree, and the test plan above is how that gets fixed.

---

## Limitations

- **Two choices only.** Left/right is the one reliable axis on this cap. The vertical eye
  signal is buried in blinks and drift, so every prompt has to be framed as a two-way choice.
- **Head still while answering.** The electrodes read where the eyes point relative to the
  head, so turning the head while keeping the eyes on a target looks like a glance. The hold is
  short (about 1.5 s in the game), but the head has to stay still for it.
- **Electrode contact.** The saline sponges at F7 and F8 need a clear path to the skin. Thick
  hair can leave them open, so impedance has to be checked before every session.
- **Settling time and per-user calibration.** The signal drifts fastest in the first minute
  after the cap goes on. Calibration waits for that, and every user calibrates at the start of
  a session (about 40 s of following a dot).
- **Latency.** The game confirms an answer after about 1.5 s of holding; the standalone
  pipeline takes about 7 s (3 s window plus 3 s dwell). Fine for a learning game, too slow for
  a cursor.
- **Tested seated, on one wearer.** All measurements so far come from one person sitting
  still. Walking, head movement and more wearers have not been tested yet, and `bridge.py` has
  run against a simulated 24-channel LSL stream, not yet on the headset live.

---

## Running it

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install numpy scipy pylsl websockets

python bridge.py --stream "NAME"      # feed the web prototype from the headset, then open index-2.html
python bridge.py --demo               # same, with a synthetic signal (no headset)
```

The pipeline lives on the `signal-processing` branch (`pip install -r requirements.txt` there):

```powershell
python -m unittest discover -s tests -t .                                  # 44 tests
python calibration.py recording.cnt --session output/session.json --reference CPz --offset-range 4 5 --offline-drift --command-calibration --output output/recovered/calibration.json
python playback_directions.py                                              # prints left / right while replaying recording.cnt
```

The web app: `cd @latest`, `npm install`, `npm run dev`, then open http://localhost:5173.

Live EEG: the laptop running the bridge and ANT's acquisition laptop must be on the same
network (ANT's router or a phone hotspot), with LSL streaming enabled in the eego software.
`--stream` takes the exact stream name; without it the first stream of type EEG is used.

---

## Team

| | |
|---|---|
| Supreme Constantine | NC State, Computer Science |
| Shradha Bhatia | NC State, Electrical and Computer Engineering |
| Matthew Sanchez | Wake Tech, Science |
| Sajan Patel | Duke, Biomedical Engineering |
| Miguel Gaido | Durham Tech, Computer Science |
