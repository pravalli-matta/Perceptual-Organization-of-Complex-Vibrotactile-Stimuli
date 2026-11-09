import numpy as np
import pandas as pd
import tkinter as tk
import time
import random
from pathlib import Path
from scipy.io import wavfile
import sounddevice as sd
# CONFIGURATION
FIXATION_TIME = 0.300
ISI = 0.150
RESPONSE_WINDOW = 2.000
ITI = 0.150
BASE_DIR = Path(__file__).resolve().parent.parent

STIMULUS_FOLDER = BASE_DIR / "stimuli" / "waveform_27"

RESULTS_DIR = BASE_DIR / "results"

RESULTS_DIR.mkdir(
    parents=True,
    exist_ok=True
)

abort_experiment = False
def emergency_exit(event):
    global abort_experiment
    if event.keysym == "Escape":
        abort_experiment = True    
pause_requested = False
def request_pause(event):

    global pause_requested
    pause_requested = True
    print("Pause requested")
# WAV FILES
wav_lookup = {}
for file in STIMULUS_FOLDER.glob("*.wav"):
    stim_id = file.name.split("_")[0]
    wav_lookup[stim_id] = str(file)
print("Number of stimuli:", len(wav_lookup))
# GENERATE TRIALS
stimuli = [f"S{i:02d}" for i in range(1, 28)]
trials = []
for i in range(len(stimuli)):
    for j in range(i, len(stimuli)):
        trials.append({
            "stimulus_A": stimuli[i],
            "stimulus_B": stimuli[j]
        })
print("Total Trials:", len(trials))
random.shuffle(trials)
trial_df = pd.DataFrame(trials)
# BLOCKS
blocks = [
    trial_df.iloc[:75].reset_index(drop=True),
    trial_df.iloc[75:150].reset_index(drop=True),
    trial_df.iloc[150:225].reset_index(drop=True),
    trial_df.iloc[225:300].reset_index(drop=True),
    trial_df.iloc[300:].reset_index(drop=True)
]
for i, block in enumerate(blocks):
    print(
        f"Block {i+1}: {len(block)}"
    )
# GUI HELPERS
def clear_widgets(root):
    for widget in root.winfo_children():
        widget.destroy()
# AUDIO
def play_wav(filepath):
    fs, data = wavfile.read(filepath)
    sd.play(
        data,
        samplerate=fs,
        blocking=True
    )
# RESPONSE COLLECTION
def collect_response(root):
    response = []
    rt = []
    start_time = time.time()
    def on_key(event):
        # NUMPAD 1 = Similar
        if event.keysym == "End":
            if len(response) == 0:
                response.append(1)
                rt.append(
                  (time.time() - start_time) * 1000
                )
        # NUMPAD 3 = Dissimilar
        elif event.keysym == "Next":
            if len(response) == 0:
                response.append(0)
                rt.append(
                    (time.time() - start_time) * 1000
                )
    root.bind("<Key>", on_key)
    while time.time() - start_time < RESPONSE_WINDOW:
        root.update()
    root.unbind("<Key>")
    if len(response) == 0:
        return None, np.nan
    return response[0], rt[0]
# PAUSE SCREEN
def pause_screen(root):
    global pause_requested
    clear_widgets(root)
    label = tk.Label(
        root,
        text=
        "Experiment Paused\n\n"
        "Press N to Resume",
        font=("Arial",24),
        fg="white",
        bg="black"
    )
    label.pack(expand=True)
    waiting = [True]
    def resume(event):
     global pause_requested
     if event.keysym.lower() == "n":
        pause_requested = False
        waiting[0] = False
    root.bind("<Key>", resume)
    while waiting[0]:
        root.update()
    root.unbind("<Key>")
    pause_requested = False
    
# SINGLE TRIAL 
def run_trial(
    root,
    stimA,
    stimB,
    participant_id,
    trial_results,
    participant_matrix
):
    clear_widgets(root)
    check_pause(
    root,
    participant_id,
    trial_results,
    participant_matrix
)
    fixation = tk.Label(
        root,
        text="+",
        font=("Arial", 36),
        fg="white",
        bg="black"
    )
    fixation.pack(expand=True)
    root.update()
    time.sleep(FIXATION_TIME)
    fixation.destroy()
    clear_widgets(root)
    root.update()
    # Stimulus A
    check_pause(
    root,
    participant_id,
    trial_results,
    participant_matrix
)
    play_wav(
        wav_lookup[stimA]
    )
    # ISI
    time.sleep(ISI)
    # Stimulus B
    check_pause(
    root,
    participant_id,
    trial_results,
    participant_matrix
)
    play_wav(
        wav_lookup[stimB]
    )
    # Response
    check_pause(
    root,
    participant_id,
    trial_results,
    participant_matrix
)
    clear_widgets(root)
    response_label = tk.Label(
        root,
        text="-",
        font=("Arial", 36),
        fg="white",
        bg="black"
    )
    response_label.pack(expand=True)
    root.focus_force()
    root.update()
    response, rt = collect_response(root)
    response_label.destroy()
    # ITI
    time.sleep(ITI)
    return response, rt
def check_pause(
    root,
    participant_id,
    trial_results,
    participant_matrix
):
    global pause_requested
    if pause_requested:
        pd.DataFrame(
            trial_results
        ).to_csv(
            RESULTS_DIR /
            f"CDT_P{participant_id}_backup_resp.csv",
            index=False
        )
        pd.DataFrame(
            participant_matrix
        ).to_csv(
            RESULTS_DIR /
            f"CDT_P{participant_id}_backup_matrix.csv",
            index=False
        )
        pause_screen(root)
# MATRIX UPDATE
def update_matrix(
    matrix,
    stimA,
    stimB,
    response
):
    i = int(stimA[1:]) - 1
    j = int(stimB[1:]) - 1
    matrix[i, j] = response
    matrix[j, i] = response
# BREAK SCREEN
def block_break(
    root,
    block_num
):
    clear_widgets(root)
    label = tk.Label(
        root,
        text=
        f"End of Block {block_num}\n\n"
        f"Take a short break\n\n"
        f"Press SPACE to continue",
        font=("Arial", 24),
        fg="white",
        bg="black"
    )
    label.pack(expand=True)
    waiting = [True]
    def continue_exp(event):
        if event.keysym == "space":
            waiting[0] = False
    root.bind("<space>", continue_exp)
    while waiting[0]:
        root.update()
    root.unbind("<space>")
# START SCREEN
def start_screen(root):
    clear_widgets(root)
    label = tk.Label(
        root,
        text=
        "Vibrotactile Similarity Experiment\n\n"
        "NUMPAD 1 = Similar\n\n"
        "NUMPAD 3 = Dissimilar\n\n"
        "Press S to begin",
        font=("Arial",24),
        fg="white",
        bg="black"
    )
    label.pack(expand=True)
    waiting = [True]
    def begin(event):
        if event.keysym.lower() == "s":
            waiting[0] = False
    root.bind("<Key>", begin)
    while waiting[0]:
        root.update()
    root.unbind("<Key>")
# END SCREEN
def end_screen(root):
    clear_widgets(root)
    label = tk.Label(
        root,
        text="Experiment Complete\n\nThank You",
        font=("Arial", 28),
        fg="white",
        bg="black"
    )
    label.pack(expand=True)
    root.update()
    time.sleep(3)
# EXPERIMENT
def start_experiment():
    participant_id = input(
        "Participant ID: "
    )
    trial_results = []
    participant_matrix = np.full(
        (27, 27),
        np.nan
    )
    root = tk.Tk()
    root.bind("<Escape>", emergency_exit)
    root.bind("p", request_pause)
    root.bind("P", request_pause)
    root.configure(
        bg="black"
    )
    root.attributes(
    "-fullscreen",
    True
)
    root.lift()
    root.focus_force()
    start_screen(root)
    root.focus_force()
    global_trial = 1
    for block_num, block in enumerate(
        blocks,
        start=1
    ):
        print(
            f"Starting Block {block_num}"
        )
        for _, row in block.iterrows():
            if abort_experiment:
                break

            stimA = row["stimulus_A"]
            stimB = row["stimulus_B"]
            response, rt = run_trial(
                root,
                stimA,
                stimB,
                participant_id,
                trial_results,
                participant_matrix
            )
            update_matrix(
                participant_matrix,
                stimA,
                stimB,
                response
            )
            trial_results.append({
                "participant":
                    participant_id,
                "block":
                    block_num,
                "trial":
                    global_trial,
                "stimulus_A":
                    stimA,
                "stimulus_B":
                    stimB,
                "response":
                    response,
                "rt_ms":
                    rt
            })
            global_trial += 1
        if abort_experiment:
            break
        # Backup after every block
        backup_df = pd.DataFrame(
            trial_results
        )
        backup_df.to_csv(
            RESULTS_DIR /
            f"CDT_P{participant_id}_backup_resp.csv",
            index=False
        )
        pd.DataFrame(
            participant_matrix
        ).to_csv(
            RESULTS_DIR /
            f"CDT_P{participant_id}_backup_matrix.csv",
            index=False
        )
        if block_num < 5:
            block_break(
                root,
                block_num
            )
    # Save full trial data
    pd.DataFrame(
        trial_results
    ).to_csv(
        RESULTS_DIR /
        f"CDT_P{participant_id}_resp.csv",
        index=False
    )
    # Save matrix
    pd.DataFrame(
        participant_matrix
    ).to_csv(
        RESULTS_DIR /
        f"CDT_P{participant_id}_matrix.csv",
        index=False
    )
    end_screen(root)
    root.destroy()
    print(
        "Experiment Complete"
    )
    if abort_experiment:
        print(
            "Experiment Aborted"
        )
    else:
        print(
            "Experiment Complete"
        )
# MAIN
if __name__ == "__main__":
    start_experiment()