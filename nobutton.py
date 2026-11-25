"""No-button version of CLARIFY: the ENTER key starts and stops each recording.

  python3 nobutton.py record steelers   saves keywords/steelers_1.wav ... steelers_5.wav
  python3 nobutton.py run               live matching, speaks the phrase with eSpeak

Same matching method as clarify_pi.py (mean of 13 MFCCs, closest reference wins).
"""
import os
import re
import subprocess
import sys
import time

import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write

RATE = 48000                 # the USB mic records at 48000, not 44100
KEYWORDS_DIR = "keywords"
PHRASES_FILE = "phrases.txt"
OUTPUT_FOLDER = "NEW_RECORDING"
TAKES = 5
last_command = {}            # remembers the last phrase used, for "on | off" toggles


def record_clip(path):
    """Record from now until ENTER is pressed, then save to path."""
    chunks = []

    def grab(indata, frames, when, status):
        chunks.append(indata.copy())

    with sd.InputStream(samplerate=RATE, channels=1, dtype="int16", callback=grab):
        input("    Recording... press ENTER to stop ")
    if not chunks:
        return False
    write(path, RATE, np.concatenate(chunks))
    return True


def record(keyword):
    os.makedirs(KEYWORDS_DIR, exist_ok=True)
    take = 1
    while take <= TAKES:
        input(f"[{take}/{TAKES}] Press ENTER, then say '{keyword}' ")
        path = os.path.join(KEYWORDS_DIR, f"{keyword}_{take}.wav")
        if record_clip(path):
            print(f"    Saved {path}")
            take += 1
    print(f"Done. Check that phrases.txt has a line starting with '{keyword}:'")


def load_phrases():
    phrases = {}
    if os.path.exists(PHRASES_FILE):
        with open(PHRASES_FILE) as f:
            for line in f:
                if ":" in line:
                    key, text = line.strip().split(":", 1)
                    phrases[key.strip().lower()] = text.strip()
    return phrases


def run():
    import librosa  # slow to load, so only loaded for live matching

    def fingerprint(path):
        y, sr = librosa.load(path, sr=None)
        return np.mean(librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13), axis=1)

    print("Loading reference recordings...")
    references = []
    for filename in sorted(os.listdir(KEYWORDS_DIR)):
        if filename.endswith(".wav"):
            name = re.sub(r"[_\-\s]*\d+$", "", os.path.splitext(filename)[0])
            references.append((name, fingerprint(os.path.join(KEYWORDS_DIR, filename))))
    if not references:
        raise SystemExit(f"No .wav files in '{KEYWORDS_DIR}'. Record some keywords first.")
    print(f"Loaded {len(references)} recordings: {', '.join(sorted({n for n, _ in references}))}")

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    temp_path = os.path.join(OUTPUT_FOLDER, "temp_recording.wav")
    while True:
        input("\nPress ENTER, then say the word (Ctrl+C to quit) ")
        if not record_clip(temp_path):
            continue
        start = time.perf_counter()
        live = fingerprint(temp_path)
        keyword = min(references, key=lambda ref: np.linalg.norm(live - ref[1]))[0]

        text = load_phrases().get(keyword, "Command not recognized.")
        if "|" in text:
            options = [o.strip() for o in text.split("|")]
            index = (last_command.get(keyword, -1) + 1) % len(options)
            last_command[keyword] = index
            text = options[index]
        print(f"TIMING stop to speech: {time.perf_counter() - start:.2f} s")
        print(f"Matched Keyword: '{keyword}' -> Output Phrase: '{text}'")
        subprocess.run(["espeak", text])


if __name__ == "__main__":
    try:
        if len(sys.argv) == 3 and sys.argv[1] == "record":
            record(sys.argv[2].strip().lower())
        elif len(sys.argv) == 2 and sys.argv[1] == "run":
            run()
        else:
            print("Usage:  python3 nobutton.py record <keyword>")
            print("        python3 nobutton.py run")
    except (KeyboardInterrupt, EOFError):
        print("\nStopped.")
