"""Record reference recordings for one keyword on the Pi.

On the terminal: python3 record_keyword.py lights
Hold the button, say the word, release. Do it five times so that the system can learn the variations in your pronunciation.
Files are saved as keywords/lights_1.wav, keywords/lights_2.wav, ...
"""
import os
import sys
import time

import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
import RPi.GPIO as GPIO

BUTTON_PIN = 17
SAMPLE_RATE = 44100
RECORDINGS_PER_KEYWORD = 5

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEYWORDS_DIR = os.path.join(BASE_DIR, "keywords")
os.makedirs(KEYWORDS_DIR, exist_ok=True)

if len(sys.argv) != 2:
    print("Usage: python3 record_keyword.py <keyword>")
    sys.exit(1)

keyword = sys.argv[1].strip().lower()

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

try:
    count = 0
    while count < RECORDINGS_PER_KEYWORD:
        print(f"[{count + 1}/{RECORDINGS_PER_KEYWORD}] Hold the button and say '{keyword}'...")

        # Wait for the button press
        while GPIO.input(BUTTON_PIN) == GPIO.HIGH:
            time.sleep(0.02)

        audio_chunks = []
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16') as stream:
            while GPIO.input(BUTTON_PIN) == GPIO.LOW:
                chunk, overflow = stream.read(1024)
                audio_chunks.append(chunk)

        if audio_chunks:
            count += 1
            file_path = os.path.join(KEYWORDS_DIR, f"{keyword}_{count}.wav")
            write(file_path, SAMPLE_RATE, np.concatenate(audio_chunks, axis=0))
            print(f"Saved {file_path}")

        time.sleep(0.3)

    print(f"Done. Now add a line for '{keyword}' to phrases.txt.")

except KeyboardInterrupt:
    print("\nStopped.")
finally:
    GPIO.cleanup()