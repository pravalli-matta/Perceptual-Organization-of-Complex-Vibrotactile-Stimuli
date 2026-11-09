import random
import tkinter as tk
from tkinter import simpledialog
from pathlib import Path

import pandas as pd
import sounddevice as sd
from scipy.io.wavfile import read


# =====================================================
# PATHS
# =====================================================

BASE_DIR = Path(__file__).resolve().parent.parent

STIMULUS_FOLDER = BASE_DIR / "stimuli" / "attack_27"

RESULTS_FOLDER = BASE_DIR / "results"
RESULTS_FOLDER.mkdir(exist_ok=True)


# =====================================================
# PARTICIPANT ID
# =====================================================

temp = tk.Tk()
temp.withdraw()

participant = simpledialog.askstring(
    "Participant ID",
    "Enter Participant ID (e.g. 001)"
)

temp.destroy()

if participant is None:
    quit()

participant = participant.strip()

csv_file = RESULTS_FOLDER / f"CDT_P{participant}_VD.csv"


# =====================================================
# LOAD STIMULI
# =====================================================

wav_files = sorted(STIMULUS_FOLDER.glob("*.wav"))

random.shuffle(wav_files)

order_df = pd.DataFrame({

    "Presentation_Order": range(1, len(wav_files)+1),

    "Stimulus_File": [f.name for f in wav_files],

    "Description": [""] * len(wav_files)

})

order_df.to_csv(csv_file, index=False)

print("Presentation order saved.")
print(csv_file)


# =====================================================
# CURRENT STIMULUS
# =====================================================

current = 0

started = False


# =====================================================
# PLAY CURRENT STIMULUS
# =====================================================

def play_current():

    filename = wav_files[current]

    fs, signal = read(filename)

    signal = signal.astype(float)

    if signal.max() > 1:
        signal /= 32767

    print(f"\nStimulus {current+1}/{len(wav_files)}")
    print(filename.name)

    sd.play(signal, fs)
    sd.wait()


# =====================================================
# START
# =====================================================

def start(event=None):

    global started

    if started:
        return

    started = True

    label.config(

        text="""
← Replay


→ Next
""",

        font=("Arial",40)

    )

    play_current()


# =====================================================
# REPLAY
# =====================================================

def replay(event=None):

    if not started:
        return

    play_current()


# =====================================================
# NEXT
# =====================================================

def next_stimulus(event=None):

    global current

    if not started:
        return

    if current < len(wav_files)-1:

        current += 1

        play_current()

    else:

        label.config(

            text="""
Finished!

Thank You
""",

            font=("Arial",40)

        )

        root.after(2000, root.destroy)


# =====================================================
# QUIT
# =====================================================

def quit_exp(event=None):

    root.destroy()


# =====================================================
# WINDOW
# =====================================================

root = tk.Tk()

root.title("Verbal Description")

root.configure(bg="black")

root.attributes("-fullscreen", True)


label = tk.Label(

    root,

    text="Press S to Start",

    bg="black",

    fg="white",

    font=("Arial",42),

    justify="center"

)

label.pack(expand=True)


# =====================================================
# KEY BINDINGS
# =====================================================

root.bind("<s>", start)
root.bind("<S>", start)

root.bind("<Left>", replay)

root.bind("<Right>", next_stimulus)

root.bind("<Escape>", quit_exp)


root.mainloop()