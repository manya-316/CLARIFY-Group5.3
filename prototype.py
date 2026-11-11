import os
import librosa
import numpy as np
import time
import sounddevice as sd
from scipy.io.wavfile import write

# --- Configuration ---
SAMPLE_RATE = 44100
import os
import re  # ADDED: used to strip the number from keyword filenames
import librosa
import numpy as np
import time
import sounddevice as sd
from scipy.io.wavfile import write

# --- Configuration ---
SAMPLE_RATE = 44100
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FOLDER = os.path.join(BASE_DIR, "NEW_RECORDING")
KEYWORDS_DIR = os.path.join(BASE_DIR, "keywords")
PHRASES_FILE = os.path.join(BASE_DIR, "phrases.txt")
last_command = {}  # ADDED (toggle): remembers the last command sent for each keyword

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
                best_match = re.sub(r"[_\-\s]*\d+$", "", best_match)  # ADDED: lights_1.wav ... lights_5.wav all count as "lights"

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

    # ADDED (toggle): if the line in phrases.txt has two phrases separated by "|",
    # alternate between them each time this keyword is said
    if "|" in output_phrase:
        options = [o.strip() for o in output_phrase.split("|")]
        index = last_command.get(keyword, -1) + 1   # next option after the one used last time
        if index >= len(options):
            index = 0
        last_command[keyword] = index               # remember what we just sent
        output_phrase = options[index]

    print(f"Matched Keyword: '{keyword}' -> Output Phrase: '{output_phrase}'")

    # Use Windows PowerShell text-to-speech to play the phrase aloud
    os.system(
        f'PowerShell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'{output_phrase}\')"')

    return output_phrase


# --- Main Execution Loop ---
try:
    # ADDED (toggle): the loop is back, because the on/off memory is lost if the program restarts every time
    while True:
        input("\nSystem ready. Press ENTER to start a 3-second recording (Ctrl+C to quit)...")
        t_start = time.perf_counter()  # ADDED FOR TESTING
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
        print(f"TIMING press to speech: {time.perf_counter() - t_start:.2f} s")  # ADDED FOR TESTING

        if matched_keyword:
            phrase(matched_keyword, phrases_file=PHRASES_FILE)
        else:
            print("No matching keyword found in database.")

except KeyboardInterrupt:
    print("\nExiting program...")
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