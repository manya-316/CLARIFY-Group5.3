import os
import re  # ADDED: used to strip the number from keyword filenames
import librosa
import numpy as np
import time
import sounddevice as sd
from scipy.io.wavfile import write
import RPi.GPIO as GPIO

# Configuration
BUTTON_PIN = 17
SAMPLE_RATE = 44100  # Standard audio sample rate
OUTPUT_FOLDER = "NEW_RECORDING"
KEYWORDS_DIR = "keywords"      # ADDED: was used below but never defined
PHRASES_FILE = "phrases.txt"   # ADDED: was used below but never defined

# Ensure the 'NEW_RECORDING' folder exists
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Setup GPIO for the button
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)


# MOVED: the two functions now come before the loop, because Python must read them before the loop can call them

def match_keyword(recorded_audio_path, keywords_dir="keywords"):
    best_match = None
    min_distance = float('inf')

    # Load and extract features for the live recording
    y_rec, sr_rec = librosa.load(recorded_audio_path, sr=None)
    mfcc_rec = librosa.feature.mfcc(y=y_rec, sr=sr_rec, n_mfcc=13)
    mfcc_rec_mean = np.mean(mfcc_rec, axis=1)

    # Iterate through reference keyword audio files
    for filename in os.listdir(keywords_dir): #Loops through every individual file and folder name located inside your specified keyword directory path.
        if filename.endswith(".wav"): #Filters the loop so it only looks at audio files ending with .wav, ignoring any other file types that might accidentally be in that folder.
            file_path = os.path.join(keywords_dir, filename) #Safely combines your folder path and the current file's name to create the full, correct file path for the audio file (regardless of operating system slashes).
            y_ref, sr_ref = librosa.load(file_path, sr=None) #Uses the librosa library to load the reference audio file into a NumPy array (y_ref), preserving its original sample rate (sr=None).
            mfcc_ref = librosa.feature.mfcc(y=y_ref, sr=sr_ref, n_mfcc=13) #Extracts Mel-frequency cepstral coefficients (MFCCs) from the reference audio. This mathematical representation captures the unique acoustic "fingerprint" or sound shape of the spoken word using 13 coefficients.
            mfcc_ref_mean = np.mean(mfcc_ref, axis=1) #Averages the MFCC matrix across the time axis, condensing the audio's feature data into a single, compact summary vector for easy comparison.

            # Calculate Euclidean distance between MFCC vectors
            distance = np.linalg.norm(mfcc_rec_mean - mfcc_ref_mean) #Calculates the Euclidean distance (the mathematical difference) between the live user recording (mfcc_rec_mean) and this reference file (mfcc_ref_mean). A smaller distance means the sounds are more similar.

            if distance < min_distance: #Checks if this reference file's distance is smaller than the smallest distance recorded so far, determining if it is a closer match than previous files.
                min_distance = distance #Updates the tracker variable with this new, smaller distance value.
                # Use filename without extension as the keyword title
                best_match = os.path.splitext(filename)[0] #Strips away the .filetype extension from the filename (e.g., turning "water.wav" into just "water"), storing it as your current best-matching keyword title.
                best_match = re.sub(r"[_\-\s]*\d+$", "", best_match)  # ADDED: also drops a trailing number, so water_1.wav ... water_5.wav all count as "water"

    return best_match


def phrase(keyword, phrases_file="phrases.txt"):
    phrase_dictionnary = {}   #Initializes an empty Python dictionary. This will act as a lookup table where the keywords point to their full, prefabricated sentences

    # Read the text document containing keyword-to-phrase mappings
    if os.path.exists(phrases_file):
        with open(phrases_file, "r") as f:
            for line in f:
                if ":" in line:
                    k, p = line.strip().split(":", 1)
                    phrase_dictionnary[k.strip()] = p.strip()

    # Retrieve the matching prefabricated phrase
    output_phrase = phrase_dictionnary.get(keyword, "Command not recognized.")
    print(f"Matched Keyword: '{keyword}' -> Output Phrase: '{output_phrase}'")

    # Use text-to-speech to play the phrase aloud via the speaker
    os.system(f'espeak "{output_phrase}"')
    return output_phrase


try:
    print("System ready. Hold the button to record...")
    while True: #this is a loop that constantly runs to check the buttons state
        if GPIO.input(BUTTON_PIN) == GPIO.LOW: # this if statement checks if he button is pressed
            print("Recording started (holding button)...")
            audio_chunks = []
            t_press = time.perf_counter()  # ADDED FOR TESTING

            # Capture audio chunks while button is held
            with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16') as stream: #Opens a continuous audio input stream from your microphone at the specified sample rate.
                while GPIO.input(BUTTON_PIN) == GPIO.LOW:
                    chunk, overflow = stream.read(1024) #Continuously reads a small snippet (1024 frames) of audio from the microphone.
                    audio_chunks.append(chunk) #Adds each new audio snippet to your list. (Once you release the button, this inner loop stops running).

            print("Button released. Saving and processing...")

            if audio_chunks:
                # Save recording
                audio_data = np.concatenate(audio_chunks, axis=0) #Merges all the individual recorded snippets into one smooth, continuous array of audio data.
                file_path = os.path.join(OUTPUT_FOLDER, "temp_recording.wav") #everytime a new recording is taken in it will overwrite the previous to ensure we don't run out of hard drive space
                write(file_path, SAMPLE_RATE, audio_data)
                print(f"Saved temporary file: {file_path}")

                # Process through your matching and phrase pipeline
                matched_keyword = match_keyword(file_path, keywords_dir=KEYWORDS_DIR)
                print(f"TIMING press to speech: {time.perf_counter() - t_press:.2f} s")  # ADDED FOR TESTING
                if matched_keyword:
                    phrase(matched_keyword, phrases_file=PHRASES_FILE)
                else:
                    print("No matching keyword found in database.")

            time.sleep(0.2)
        time.sleep(0.05)

except KeyboardInterrupt:
    print("\nExiting program...")
    GPIO.cleanup()