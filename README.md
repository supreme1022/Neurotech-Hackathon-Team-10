# PhoniFide: How to run the EEG pipeline

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
