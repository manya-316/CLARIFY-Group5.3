"""Record reference recordings for one keyword on a laptop.

Run:  python record_keyword_laptop.py
Type the keyword, then press ENTER before each recording and say the word.
Files are saved as keywords/lights_1.wav, keywords/lights_2.wav, ...
"""
import os

import sounddevice as sd
from scipy.io.wavfile import write

SAMPLE_RATE = 44100
SECONDS = 3                  # same length as the live recording in clarify_laptop.py
RECORDINGS_PER_KEYWORD = 5

# Saves into a 'keywords' folder next to this script.
# To save straight into the folder clarify_laptop.py uses, paste that path here instead.
KEYWORDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keywords")
os.makedirs(KEYWORDS_DIR, exist_ok=True)

keyword = input("Keyword to record (for example: lights): ").strip().lower()
if not keyword:
    raise SystemExit("No keyword entered.")

for count in range(1, RECORDINGS_PER_KEYWORD + 1):
    input(f"[{count}/{RECORDINGS_PER_KEYWORD}] Press ENTER, then say '{keyword}'...")
    print("Recording...")
    audio_data = sd.rec(int(SECONDS * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='int16')
    sd.wait()

    file_path = os.path.join(KEYWORDS_DIR, f"{keyword}_{count}.wav")
    write(file_path, SAMPLE_RATE, audio_data)
    print(f"Saved {file_path}")

print(f"\nDone. Make sure phrases.txt has a line starting with '{keyword}:'")