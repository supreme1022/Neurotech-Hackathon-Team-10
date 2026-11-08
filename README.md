# PhoniFide: How to run the EEG pipeline

> **About this branch.** `drift-tracking` is the pipeline as of commit 9f8e111 plus the causal
> drift-tracking additions (baseline tracking, horizontal-only calibration, settling-repetition
> skip, `estimate_offset.py`) that produced the results quoted in the main README. The saved
> outputs of those runs are in `results/sesh2/`. The `signal-processing` branch continued
> separately with an offline recovery mode for the same recording.

**Record the eyes following the dot → create a calibration file → replay the EEG to see predicted gaze directions.**

## 1. Open the project

Open **Anaconda PowerShell Prompt** and paste:

```powershell
Set-Location "C:\Users\sajan\Documents\github_repos\Neurotech-Hackathon-Team-10"
conda activate neurotech-hackathon
```

Keep using this window for the commands below. This computer already has the required packages.

## 2. Record the participant

If you already recorded with the updated GUI, saved its session file, and measured the start time described below, skip to step 3.

1. Start EEG recording in the ANT software. Include channels **F7, F8, Fp1, and Fp2**.
2. Run this command:

   ```powershell
   python calibration_GUI.py --output output/session.json
   ```

3. Check the recording confirmation box in the GUI, then press **Space**.
4. Have the participant follow the dot without moving their head. During BLINK instructions, blink about once per second while looking at the center.
5. Wait about **4 minutes**, until the GUI says calibration is complete. Then stop ANT recording.

The GUI saves `output/session.json`. **Keep it: it tells calibration when each target appeared.** The GUI does not start or stop ANT recording.

### One timing detail you must record

You need the EEG recording's elapsed time when the **first dot appears**. This is called the **offset**.

**Example:** EEG recording starts, then the first dot appears 12.34 seconds later. Your offset is `12.34`.

Measure this using a recording of both the GUI and the EEG elapsed-time display, or another verified timing method. It is **not** the time you press Space; the GUI has a countdown. Do not guess the offset or assume it is zero.

If you already recorded but have neither this timing information nor saved acquisition markers, the scripts cannot reliably match EEG to the targets. See [timing alternatives](docs/advanced.md#synchronization-is-required).

## 3. Put the recording in this folder

For these examples, name your CNT file **`recording.cnt`** and place it alongside `calibration.py`. Keep the matching GUI log at **`output/session.json`**.

You should have:

```text
Neurotech-Hackathon-Team-10/
    recording.cnt
    calibration.py
    calibration_GUI.py
    real_time_classification.py
    output/
        session.json
```

If you ran the GUI on another computer, copy its session file here too.

## 4. Create the calibration file

Paste this command, replacing **`12.34` with your measured offset**:

```powershell
python calibration.py recording.cnt --session output/session.json --reference CPz --offset 12.34
```

`CPz` must be the reference electrode used by ANT during recording. Replace it if your acquisition settings use another reference.

Wait for **`Calibration saved: output\calibration.json`**. That file contains the settings the classifier needs. A report and a diagnostic image are also saved in `output`.

If calibration fails, read the error before continuing. A failed run does not produce a new usable calibration.

## 5. See the gaze predictions

```powershell
python real_time_classification.py playback recording.cnt --calibration output/calibration.json --reference CPz --plot
```

Use the same reference as step 4. This replays your saved recording and shows the predicted gaze direction. The participant does not need to keep wearing the cap.

- Initial **WARMUP** messages are normal.
- Direction detection can take about **6 seconds** after a gaze change.
- Predictions and a summary are saved automatically in `output`.
- Press **Ctrl+C** to stop early.

To classify another CNT recording from the same participant and cap setup, replace `recording.cnt` in this command with that file's name. Keep the same sampling rate, acquisition settings, and reference.

## Session 2 recipe (Nov 7, 5:54 PM recording): what actually worked

The 4-minute recording (`recording.cnt` in this branch, the same file as on the
`signal-processing` branch) needed three things the default pipeline does not do. All three are options that
default to the original behaviour, and the test suite covers them (`tests/test_drift.py`).

1. **No session JSON, no measured offset.** `estimate_offset.py` matches the horizontal eye
   signal against the dot schedule and found the default protocol (10 s holds) starting
   **4.52 s** into the recording (r = +0.55). It writes a reconstructed session file.
2. **Electrode drift.** The signal drifted about 800 uV over the session, several times the
   size of a glance, so one fixed baseline cannot work, and a Butterworth high-pass destroys
   10-second holds. `--baseline-track 2` lets the baseline follow the signal only while gaze
   is at CENTER (frozen during a glance). Live, it starts from the first window and
   `--baseline-rescue 15` re-centres if a "glance" lasts longer than any real one.
3. **The first repetition is settling time.** Fresh gel drifted about 20 uV/s during the
   first minute, which no tracker can follow. `--skip-repeats 1` fits on repetition 2 and
   holds out repetition 3. UP/DOWN are not separable on this cap (frontal vertical signal is
   swamped by blinks and drift), so calibrate horizontal only with `--directions RIGHT,LEFT`.

```powershell
python estimate_offset.py recording.cnt --output output/sesh2_session.json --plot output/sesh2_match.png
python calibration.py recording.cnt --session output/sesh2_session.json --reference CPz --offset 4.52 --directions RIGHT,LEFT --baseline-track 2 --baseline-rescue 15 --skip-repeats 1 --output output/sesh2_calibration.json
python real_time_classification.py playback recording.cnt --calibration output/sesh2_calibration.json --reference CPz --plot
```

Result on the held-out repetition: 100% window recall for CENTER, RIGHT and LEFT, and the
live classifier detected 2/2 glances with 0 false activations. Replaying the whole recording:
repetitions 2 and 3 gave 4/4 glances, 0 false activations, about 6 s after the dot moved
(3 s window + 3 s dwell). Repetition 1 (settling) gave 2 false LEFT calls, so live sessions
should wait a minute after the cap goes on before trusting detections. Thresholds came out
near +136 uV (RIGHT) and -145 uV (LEFT); glances measured roughly +190 / -200 uV.

The files these commands produced are in `results/sesh2/` (reconstructed session file,
calibration JSON and report, diagnostics plot, offset-match plot, playback log and prediction
summary), so the numbers above can be checked without re-running anything.

## If something goes wrong

| Problem | What to do |
|---|---|
| Missing session file | Copy the JSON saved by the GUI during this exact recording. |
| Recording too short | Export the full protocol. The existing 2.855-second example CNT is too short. |
| Cannot align session | Check the matching session file and measured offset. |
| Missing channels | Check the channel names. Prefixed names such as `EEG F7` need a [channel map](docs/advanced.md#2-fit-and-validate-calibration). |
| Calibration quality failed | Check timing and signal quality; you may need a new recording. |
| Output already exists | Use new filenames for another run; see the advanced guide for output options. |

For installation on another computer, live EEG, acquisition markers, tests, or technical details, see the **[advanced guide](docs/advanced.md)**.
