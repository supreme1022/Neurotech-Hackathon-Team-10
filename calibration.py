import mne
import numpy as np
import time
import matplotlib.pyplot as plt

def run_virtual_calibration(edf_path):
    print(f"Loading {edf_path}...")
    # 1. Load the EDF file
    raw = mne.io.read_raw_edf(edf_path, preload=True, verbose=False)
    sfreq = raw.info['sfreq']
    
    # 2. Specialized Filtering (0.01 Hz High-pass, 5.0 Hz Low-pass)
    # This prevents the DC voltage shift of sustained gaze from drifting back to zero
    print("Applying 0.01 - 5.0 Hz bandpass filter...")
    raw.filter(l_freq=0.01, h_freq=5.0, verbose=False)
    
    # 3. Extract channels for Virtual EOG
    # MNE returns data in Volts; we extract F7, F8, Fp1, Fp2
    f7 = raw.get_data(picks=['F7'])[0]
    f8 = raw.get_data(picks=['F8'])[0]
    fp1 = raw.get_data(picks=['Fp1'])[0]
    fp2 = raw.get_data(picks=['Fp2'])[0]
    
    # Calculate Virtual Axes
    # Horizontal: Right gaze = positive voltage shift, Left gaze = negative
    h_eog = f8 - f7 
    # Vertical: Up gaze = positive voltage shift, Down gaze = negative
    v_eog = (fp1 + fp2) / 2.0 
    
    # 4. Virtual Real-Time Playback Setup
    window_size_sec = 0.5  # 500 ms window
    step_size_sec = 0.1    # 100 ms step
    
    window_size_samples = int(window_size_sec * sfreq)
    step_size_samples = int(step_size_sec * sfreq)
    total_samples = len(h_eog)
    
    h_means, v_means, timestamps = [], [], []
    
    print("\nStarting Virtual Real-Time Playback...")
    print("Streaming in 100ms chunks (press Ctrl+C to abort and plot early)")
    
    try:
        for start in range(0, total_samples - window_size_samples, step_size_samples):
            end = start + window_size_samples
            
            # Extract current chunk
            h_chunk = h_eog[start:end]
            v_chunk = v_eog[start:end]
            
            # Calculate mean amplitude (convert from Volts to microVolts)
            h_mean_uv = np.mean(h_chunk) * 1e6
            v_mean_uv = np.mean(v_chunk) * 1e6
            
            h_means.append(h_mean_uv)
            v_means.append(v_mean_uv)
            
            current_time_sec = start / sfreq
            timestamps.append(current_time_sec)
            
            # Simulate real-time delay (uncomment to actually wait)
            # time.sleep(step_size_sec)
            
            # Print live feed every 1 second of data
            if (start % int(sfreq)) < step_size_samples:
                print(f"Time: {current_time_sec:05.1f}s | H-Mean: {h_mean_uv:>6.1f} µV | V-Mean: {v_mean_uv:>6.1f} µV")
                
    except KeyboardInterrupt:
        print("\nPlayback interrupted by user. Plotting gathered data...")

    # 5. Visualize to Determine Thresholds
    print("\nPlotting Virtual EOG means to determine classification thresholds...")
    plt.style.use('dark_background') # Better for live hackathon environments
    plt.figure(figsize=(12, 6))
    
    plt.plot(timestamps, h_means, label='Horizontal (Right = +, Left = -)', color='cyan')
    plt.plot(timestamps, v_means, label='Vertical (Up = +, Down = -)', color='magenta')
    
    plt.title('Phase 1 Calibration: Identify µV Thresholds for Sustained Gaze')
    plt.xlabel('Time in Recording (seconds)')
    plt.ylabel('Mean Amplitude (µV)')
    plt.axhline(0, color='white', linestyle='-', alpha=0.3)
    
    # Optional helper lines
    plt.axhline(30, color='cyan', linestyle='--', alpha=0.5, label='Example Threshold (+30 µV)')
    plt.axhline(-30, color='cyan', linestyle='--', alpha=0.5)
    
    plt.legend()
    plt.grid(True, alpha=0.2)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # Replace with your actual calibration EDF file from the USB
    run_virtual_calibration('calibration_recording.edf')