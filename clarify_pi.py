import os
import time

import librosa
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
import RPi.GPIO as GPIO

BUTTON_PIN = 17
SAMPLE_RATE = 44100 

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FOLDER = os.path.join(BASE_DIR, "NEW_RECORDING")
KEYWORDS_DIR = os.path.join(BASE_DIR, "keywords")
PHRASES_FILE = os.path.join(BASE_DIR, "phrases.txt")

os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def match_keyword(recorded_audio_path, keywords_dir=KEYWORDS_DIR):
    best_match = None
    min_distance = float('inf')

    y_rec, sr_rec = librosa.load(recorded_audio_path, sr=None)
    mfcc_rec = librosa.feature.mfcc(y=y_rec, sr=sr_rec, n_mfcc=13)
    mfcc_rec_mean = np.mean(mfcc_rec, axis=1)

    for filename in os.listdir(keywords_dir):
        if filename.endswith(".wav"):
            file_path = os.path.join(keywords_dir, filename)
            y_ref, sr_ref = librosa.load(file_path, sr=None)
            mfcc_ref = librosa.feature.mfcc(y=y_ref, sr=sr_ref, n_mfcc=13)
            mfcc_ref_mean = np.mean(mfcc_ref, axis=1)

            distance = np.linalg.norm(mfcc_rec_mean - mfcc_ref_mean)

            if distance < min_distance:
                min_distance = distance
                best_match = os.path.splitext(filename)[0]

    return best_match


def phrase(keyword, phrases_file=PHRASES_FILE):
    phrase_dictionary = {}

    if os.path.exists(phrases_file):
        with open(phrases_file, "r") as f:
            for line in f:
                if ":" in line:
                    k, p = line.strip().split(":", 1)
                    phrase_dictionary[k.strip()] = p.strip()

    output_phrase = phrase_dictionary.get(keyword, "Command not recognized.")
    print(f"Matched Keyword: '{keyword}' -> Output Phrase: '{output_phrase}'")

    os.system(f'espeak "{output_phrase}"')
    return output_phrase

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

try:
    print("System ready. Hold the button to record...")
    while True:
        if GPIO.input(BUTTON_PIN) == GPIO.LOW:
            print("Recording started (holding button)...")
            audio_chunks = []
            t_press = time.perf_counter()

            with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16') as stream:
                while GPIO.input(BUTTON_PIN) == GPIO.LOW:
                    chunk, overflow = stream.read(1024)
                    audio_chunks.append(chunk)

            t_release = time.perf_counter()
            print("Button released. Saving and processing...")

            if audio_chunks:
                audio_data = np.concatenate(audio_chunks, axis=0)
                file_path = os.path.join(OUTPUT_FOLDER, "temp_recording.wav")
                write(file_path, SAMPLE_RATE, audio_data)

                matched_keyword = match_keyword(file_path)
                t_matched = time.perf_counter()

#use for deliverable F
                print(f"TIMING  recording: {t_release - t_press:.2f} s | "
                      f"processing: {t_matched - t_release:.2f} s | "
                      f"press to speech: {t_matched - t_press:.2f} s")

                if matched_keyword:
                    phrase(matched_keyword)
                else:
                    print("No matching keyword found in database.")

            time.sleep(0.2)
        time.sleep(0.05)

except KeyboardInterrupt:
    print("\nExiting program...")
finally:
    GPIO.cleanup()