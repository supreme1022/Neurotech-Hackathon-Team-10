import mne
import numpy as np
import time
import matplotlib.pyplot as plt

def run_realtime_classifier(edf_path, h_thresh, v_thresh, var_thresh):
    print(f"Loading {edf_path}...")
    raw = mne.io.read_raw_edf(edf_path, preload=True, verbose=False)
    sfreq = raw.info['sfreq']
    
    # 1. Apply specialized filters
    raw.filter(l_freq=0.01, h_freq=5.0, verbose=False)
    
    # 2. Extract Virtual EOG Channels
    f7, f8 = raw.get_data(picks=['F7'])[0], raw.get_data(picks=['F8'])[0]
    fp1, fp2 = raw.get_data(picks=['Fp1'])[0], raw.get_data(picks=['Fp2'])[0]
    
    h_eog = f8 - f7 
    v_eog = (fp1 + fp2) / 2.0 
    
    # 3. Window setup for the 3-second rule
    window_sec = 3.0  # Must hold gaze for 3 seconds
    step_sec = 0.1    # Update classification every 100ms
    
    window_samples = int(window_sec * sfreq)
    step_samples = int(step_sec * sfreq)
    total_samples = len(h_eog)
    
    # 4. Live Plotting Setup
    plt.ion() # Enable interactive mode for live plotting
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    fig.canvas.manager.set_window_title('Neurotech Hackathon: Live Gaze Classifier')
    
    # We will display a scrolling window of the last 10 seconds
    display_sec = 10.0 
    display_samples = int(display_sec * sfreq)
    
    h_line, = ax1.plot([], [], color='cyan', lw=1.5)
    v_line, = ax2.plot([], [], color='magenta', lw=1.5)
    
    ax1.set_xlim(0, display_sec)
    ax2.set_xlim(0, display_sec)
    
    ax1.set_ylim(-100, 100) # Adjust based on your Phase 1 findings
    ax2.set_ylim(-100, 100)
    
    ax1.set_title("Horizontal EOG (F8 - F7)")
    ax2.set_title("Vertical EOG (Mean Frontal)")
    ax1.axhline(h_thresh, color='white', linestyle='--', alpha=0.5)
    ax1.axhline(-h_thresh, color='white', linestyle='--', alpha=0.5)
    ax2.axhline(v_thresh, color='white', linestyle='--', alpha=0.5)
    ax2.axhline(-v_thresh, color='white', linestyle='--', alpha=0.5)
    
    # UI Text element for live classification
    class_text = fig.text(0.5, 0.95, 'INITIALIZING...', 
                          ha='center', va='center', fontsize=20, 
                          color='yellow', weight='bold')
    
    plt.style.use('dark_background')
    plt.tight_layout(rect=[0, 0, 1, 0.9])
    
    print("\nStarting Live Classification Feed...")
    
    # 5. The Virtual Real-Time Loop
    try:
        # Start iterating only after we have at least 1 full window of data
        for current_end in range(window_samples, total_samples, step_samples):
            current_start = current_end - window_samples
            
            # Grab the 3-second evaluation window
            h_window = h_eog[current_start:current_end] * 1e6 # Convert to µV
            v_window = v_eog[current_start:current_end] * 1e6
            
            # Calculate features
            h_mean = np.mean(h_window)
            v_mean = np.mean(v_window)
            h_var = np.var(h_window)
            v_var = np.var(v_window)
            
            # --- CLASSIFICATION LOGIC ---
            classification = "CENTER / NEUTRAL"
            text_color = 'white'
            
            # 1st Priority: Is the eye moving or blinking? (High variance)
            if h_var > var_thresh or v_var > var_thresh:
                classification = "TRANSITION / BLINK"
                text_color = 'orange'
            
            # 2nd Priority: Gaze is stable (Low variance), check amplitude thresholds
            else:
                if h_mean > h_thresh:
                    classification = "LOOKING RIGHT"
                    text_color = 'cyan'
                elif h_mean < -h_thresh:
                    classification = "LOOKING LEFT"
                    text_color = 'cyan'
                elif v_mean > v_thresh:
                    classification = "LOOKING UP"
                    text_color = 'magenta'
                elif v_mean < -v_thresh:
                    classification = "LOOKING DOWN"
                    text_color = 'magenta'
                    
            # --- UPDATE VISUALIZATION ---
            class_text.set_text(f"STATE: {classification}")
            class_text.set_color(text_color)
            
            # Determine data for the scrolling plot (last 10 seconds)
            plot_start = max(0, current_end - display_samples)
            time_axis = np.linspace(0, (current_end - plot_start)/sfreq, current_end - plot_start)
            
            h_line.set_data(time_axis, h_eog[plot_start:current_end] * 1e6)
            v_line.set_data(time_axis, v_eog[plot_start:current_end] * 1e6)
            
            # Dynamically adjust X-axis for scrolling effect
            ax1.set_xlim(0, max(display_sec, time_axis[-1]))
            ax2.set_xlim(0, max(display_sec, time_axis[-1]))
            
            fig.canvas.draw()
            fig.canvas.flush_events()
            
            # Force the script to run at real-world speed
            time.sleep(step_sec)
            
    except KeyboardInterrupt:
        print("\nLive classification stopped.")
        plt.ioff()
        plt.show()

if __name__ == "__main__":
    # Replace these values with the exact microvolt numbers you found in Phase 1
    CALIBRATED_H_THRESH = 30.0    # µV threshold for Left/Right
    CALIBRATED_V_THRESH = 25.0    # µV threshold for Up/Down
    CALIBRATED_VAR_THRESH = 200.0 # Variance limit (spikes over this = saccade/blink)
    
    run_realtime_classifier('task_recording.edf', 
                            CALIBRATED_H_THRESH, 
                            CALIBRATED_V_THRESH, 
                            CALIBRATED_VAR_THRESH)