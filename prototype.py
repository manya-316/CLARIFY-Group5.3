import os
import librosa
import numpy as np
import time
import sounddevice as sd
from scipy.io.wavfile import write

# --- Configuration ---
SAMPLE_RATE = 44100
OUTPUT_FOLDER = r"C:\Users\nettr\Desktop\University of Ottawa\Engineering Design\design 2\NEW_RECORDING"
KEYWORDS_DIR = r"C:\Users\nettr\Desktop\University of Ottawa\Engineering Design\design 2\keywords"
PHRASES_FILE = r"C:\Users\nettr\Desktop\University of Ottawa\Engineering Design\design 2\phrases.txt"

# Ensure the 'NEW_RECORDING' folder exists
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# --- Functions (Must be defined before they are used) ---
def match_keyword(recorded_audio_path, keywords_dir="keywords"):
    best_match = None
    min_distance = float('inf')

    # Load and extract features for the live recording
    y_rec, sr_rec = librosa.load(recorded_audio_path, sr=None)
    mfcc_rec = librosa.feature.mfcc(y=y_rec, sr=sr_rec, n_mfcc=13)
    mfcc_rec_mean = np.mean(mfcc_rec, axis=1)

    # Iterate through reference keyword audio files
    for filename in os.listdir(keywords_dir):
        if filename.endswith(".wav"):
            file_path = os.path.join(keywords_dir, filename)
            y_ref, sr_ref = librosa.load(file_path, sr=None)
            mfcc_ref = librosa.feature.mfcc(y=y_ref, sr=sr_ref, n_mfcc=13)
            mfcc_ref_mean = np.mean(mfcc_ref, axis=1)

            # Calculate Euclidean distance between MFCC vectors
            distance = np.linalg.norm(mfcc_rec_mean - mfcc_ref_mean)

            if distance < min_distance:
                min_distance = distance
                best_match = os.path.splitext(filename)[0]

    return best_match


def phrase(keyword, phrases_file="phrases.txt"):
    phrase_dictionary = {}

    # Read the text document containing keyword-to-phrase mappings
    if os.path.exists(phrases_file):
        with open(phrases_file, "r") as f:
            for line in f:
                if ":" in line:
                    k, p = line.strip().split(":", 1)
                    phrase_dictionary[k.strip()] = p.strip()

    # Retrieve the matching prefabricated phrase
    output_phrase = phrase_dictionary.get(keyword, "Command not recognized.")
    print(f"Matched Keyword: '{keyword}' -> Output Phrase: '{output_phrase}'")

    # Use Windows PowerShell text-to-speech to play the phrase aloud
    os.system(
        f'PowerShell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'{output_phrase}\')"')

    return output_phrase


# --- Main Execution Loop ---
# --- Main Execution Loop ---
try:
    # Removed the 'while True:' loop so it only runs exactly once per test
    input("\nSystem ready. Press ENTER to start a 3-second recording...")
    print("Recording...")

    # Record a fixed 3-second clip for laptop testing
    audio_data = sd.rec(int(3 * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='int16')
    sd.wait()
    print("Recording finished. Processing...")

    # Save temporary recording
    file_path = os.path.join(OUTPUT_FOLDER, "temp_recording.wav")
    write(file_path, SAMPLE_RATE, audio_data)

    # Process through your matching and phrase pipeline
    matched_keyword = match_keyword(file_path, keywords_dir=KEYWORDS_DIR)

    if matched_keyword:
        phrase(matched_keyword, phrases_file=PHRASES_FILE)
    else:
        print("No matching keyword found in database.")

except KeyboardInterrupt:
    print("\nExiting program...")