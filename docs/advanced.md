# Advanced guide

For the basic recording workflow, start with [the README](../README.md).

Gaze calibration and classification from ANT Neuro EEG channels F7, F8, Fp1
and Fp2. The pipeline supports ANT CNT / EDF recordings and an existing LSL EEG
stream. It detects eye-movement signals present in frontal EEG; it does not
estimate screen coordinates.

## Setup

Python 3.10+ is required. On this Windows machine, use the existing conda
environment so SciPy can find its numerical DLLs:

```powershell
conda activate neurotech-hackathon
python -m pip install -r requirements.txt
# Optional, for EEG streaming or calibration marker output:
python -m pip install -r requirements-live.txt
```

The existing environment already contains these libraries. Installation is only
needed when setting up a new environment. Alternatively prefix commands with
`conda run --no-capture-output -n neurotech-hackathon`.

## 1. Collect a complete labeled session

Start ANT recording externally before starting the GUI protocol. The GUI does
not control ANT acquisition or verify that its recorder is running.

```powershell
python calibration_GUI.py --output output/session.json
# If your acquisition setup can record the marker stream:
python calibration_GUI.py --output output/session_lsl.json --lsl-markers
```

Confirm external recording in the GUI and press Space. Follow each dot with your
eyes while keeping your head still. During BLINK trials, blink about once per
second while looking at center. Escape aborts and saves an unusable partial
session rather than labeling it complete.

Defaults take about 4 minutes: an 8-second initial center period, three
repetitions with 10-second direction holds, 6-second center/blink holds, and a
final center hold. Direction order rotates between repetitions. Options include
`--repetitions`, `--hold`, `--center`, `--blink`, `--warmup`, `--countdown`
and `--windowed`. Longer holds may be needed for noisy recordings.

The JSON log checkpoints every target change, including actual software onset
times, measured durations, screen geometry, completion state and marker IDs.
Times are measured after Tk has processed display updates; they are not
photodiode measurements of physical display onset. Reproduce head position,
viewing distance, electrode placement and screen geometry in subsequent use.

### Synchronization is required

Use one of these explicit alignment methods:

1. **Acquisition markers:** with `--lsl-markers`, the GUI publishes
   `EOGCalibrationMarkers`. Each sample is an exact marker string such as
   `EOG|<session_id>|<trial_id>|RIGHT`. Configure and verify the recorder so
   these strings, including the END marker, appear as annotations in the
   exported CNT/EDF file. Calibration requires every marker once, in order,
   with durations agreeing within 250 ms.
2. **Verified recording offset:** independently measure the recording time
   of the first displayed center target and pass it as `--offset`.
   For example, if the first target appears 12.34 seconds into the EEG,
   supply `--offset 12.34`.

**Publishing LSL markers does not automatically embed them in ANT CNT.**
A wall-clock timestamp or an approximately simultaneous start is insufficient.
This project does not provide an ANT hardware-trigger driver or import XDF.
If your recorder stores markers separately, use a verified offset or export
the exact annotations into a supported recording.

The repository's existing `Team10_Session1_2026-11-07_15-31-01.cnt`
is readable and has the required channels, but contains only 2.855 seconds.
It cannot calibrate this protocol.

## 2. Fit and validate calibration

Reference is the actual acquisition reference, not a new software rereference.
For the supplied CNT header it is CPz; check your settings for new recordings.

```powershell
python calibration.py recording.cnt --session output/session.json --reference CPz --offset 12.34 --output output/calibration.json
# With verified acquisition annotations, omit --offset:
python calibration.py recording.cnt --session output/session_lsl.json --reference CPz --output output/calibration.json
```

Both CNT and EDF are accepted. Channel matching ignores case and surrounding
spaces. For different labels, provide a JSON mapping:

```json
{"F7": "EEG F7", "F8": "EEG F8", "Fp1": "EEG Fp1", "Fp2": "EEG Fp2"}
```

Pass its filename with `--channel-map channels.json`.

Calibration discards the first two seconds of each target, trims its final
250 ms, and uses only three-second windows entirely within the remaining target.
The initial center period is excluded from fitting. All samples in BAD spans
are invalid; impedance/edge markers reset processing.

All final-repetition trials are held out before fitting. Training estimates
center offsets, directional polarity and asymmetric thresholds, plus separate
horizontal/vertical variance limits. Directions must separate from other targets
with at least a 1 uV training margin. Ambiguous simultaneous axis crossings are
rejected rather than giving horizontal gaze priority.

Default acceptance requires at least 80% recall for every state, including
CENTER and BLINK, and at least 80% majority-trial accuracy on held-out data.
A second validation runs the actual dwell classifier: directional trial recall
must meet the same minimum, with zero incorrect/center/blink activations.
Thresholds are engineering defaults, not established human-performance claims.
Do not lower them simply to make a bad recording pass.

A successful run writes:

- `calibration.json`: versioned, validated parameters and processing settings.
- `calibration.report.json`: parameters, per-state confusion counts,
  held-out trials, false activations and detection latencies.
- `calibration.features.csv`: labeled training/validation features.
- `calibration.diagnostics.png`: centered means, variance limits and targets.

When a fitted model fails validation, diagnostics/report/features are saved but
no usable calibration is written. Earlier fitting/input failures stop with a
specific error. Existing calibration files require `--overwrite`;
a failed overwrite attempt preserves the previous calibration.

Use `--no-plot` to skip PNG generation. Processing options include
`--lowpass`, `--highpass`, `--warmup`, `--settle`, `--trim-end`
and `--minimum-accuracy`. Changing preprocessing requires recalibration.

## 3. Classify a recording

```powershell
python real_time_classification.py playback task_recording.cnt --calibration output/calibration.json --reference CPz --plot
# Unpaced processing for evaluation:
python real_time_classification.py playback task_recording.edf --calibration output/calibration.json --reference CPz --speed 0 --output output/task_predictions.csv
```

The reference and sampling rate must match calibration. Reference is an operator
assertion; the software cannot verify the physical wiring. Acquisition hardware
filters, reference, channel derivations and electrode positions must also remain
consistent. Output defaults to a new timestamped CSV plus a summary JSON.
Existing prediction CSVs are never overwritten.

CSV rows contain source-relative time, quality, candidate, active state, dwell
progress, one-time activation events, means in uV and variances in uV^2.
The summary counts activations; those counts alone do not establish accuracy.

## 4. Classify a live LSL stream

ANT acquisition must already publish EEG to LSL through a compatible acquisition
application or bridge. This code is an LSL consumer, not an amplifier driver.

```powershell
python real_time_classification.py live --stream-name "ANT EEG" --calibration output/calibration.json --reference CPz --plot
# Alternatively choose the exact source ID; override units only after checking scaling:
python real_time_classification.py live --source-id "your-source-id" --calibration output/calibration.json --reference CPz --units uV --duration 120
```

The selected stream must be unique, regularly sampled, and contain channel
labels and recognized units. Units may come from each channel's LSL metadata or
an explicit `--units V`, `mV`, or `uV` override. Incorrect units can invalidate
all thresholds. Use `--channel-map` when the stream labels differ.

Incoming timestamps are corrected to the local LSL clock without dejittering
away acquisition gaps. Default maximum sample age is 0.5 seconds; stale samples
are discarded, dropouts reset dwell/filter history, and ten seconds without
fresh data exits with an error. Configure `--max-latency` and
`--idle-timeout` for the acquisition system. Ctrl+C or closing the optional
plot ends classification and preserves the prediction log.

The adapter has mock-based tests and an optional local transport smoke test
(`python -m tests.lsl_smoke`). Verify the actual ANT bridge, channel scaling,
clock behavior and dropout behavior before relying on hardware operation.

## Processing and dwell behavior

`eog_pipeline.py` implements one stateful causal fourth-order Butterworth
filter for all modes. By default it is low-pass only at 5 Hz: sustained gaze
offsets are preserved, and center subtraction removes the measured baseline.
There is no 330-second FIR applied to a short recording. Baseline drift remains
possible; re-center/recalibrate if neutral no longer matches the recorded baseline.

Two seconds are discarded after every reset, followed by a complete three-second
feature window. Means and variances update approximately every 100 ms.
The axes are `F8 - F7` and `(Fp1 + Fp2) / 2`, with calibration-determined
polarity and baseline. The vertical axis retains the acquisition reference.

A candidate must pass full-window stability checks, agree with the most recent
200 ms, and remain eligible continuously for three seconds before activation.
Hysteresis reduces threshold chatter. Neutral, blinks, ambiguity, transitions,
invalid samples and gaps reset dwell; activation is emitted once per continuous
hold. Full-window stability plus dwell can make latency approximately six seconds
after a transition, rather than exactly three. Diagnostics report measured latency.

The frontal EEG combination may fail to separate vertical gaze from artifacts.
The fitter reports that failure; collecting dedicated EOG channels or changing
the axis definition requires an explicit implementation change and recalibration.

## Verification and synthetic demonstration

Tests use Python's standard unittest runner; no pytest dependency is needed.

```powershell
python -B -m unittest discover -v
# Generate explicitly synthetic fixtures, then exercise both CLIs and PNG output:
python -m tests.synthetic --output output/demo
python calibration.py output/demo/recording.edf --session output/demo/session.json --reference CPz --offset 0 --output output/demo/calibration.json
python real_time_classification.py playback output/demo/recording.edf --calibration output/demo/calibration.json --reference CPz --speed 0 --output output/demo/predictions.csv
```

Tests cover causal chunk equivalence, warm-up, missing samples, alignment,
baseline/polarity fitting, separation failures, held-out leakage, quality rejection,
dwell timing, blink resets, ambiguous gaze, unit conversion, GUI completion/abort
logging, saved artifacts, and the local short CNT when available.

Synthetic success establishes software behavior, not performance on a person.
Collect a new complete calibration and separate labeled task recordings to measure
real directional accuracy, blink rejection, false activations and latency.
