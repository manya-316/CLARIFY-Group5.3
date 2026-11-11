"""Test the keyword matching on the Pi WITHOUT a microphone, speaker or button.

It runs every .wav in the 'test_recordings' folder through the same matching
method as clarify_pi.py, and reports accuracy and processing time.

Run:  python3 test_on_pi.py
"""
import os
import re
import time

import librosa
import numpy as np

KEYWORDS_DIR = "keywords"
TEST_DIR = "test_recordings"


def keyword_from_filename(filename):
    """lights_3.wav -> lights ; lights_test2.wav -> lights"""
    stem = os.path.splitext(filename)[0]
    stem = re.sub(r"[_\-\s]*test[_\-\s]*\d*$", "", stem)
    return re.sub(r"[_\-\s]*\d+$", "", stem)


def match_keyword(recorded_audio_path, keywords_dir=KEYWORDS_DIR):
    # Same method as clarify_pi.py
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
                best_match = keyword_from_filename(filename)

    return best_match


test_files = sorted(f for f in os.listdir(TEST_DIR) if f.endswith(".wav"))
if not test_files:
    print(f"No .wav files found in '{TEST_DIR}'.")
    raise SystemExit(1)

# The first call is slower because the libraries warm up, so run one untimed
match_keyword(os.path.join(TEST_DIR, test_files[0]))

correct = 0
times = []
print(f"{'File':<28}{'Expected':<14}{'Matched':<14}{'Time (s)':<10}Result")
for filename in test_files:
    expected = keyword_from_filename(filename)
    start = time.perf_counter()
    matched = match_keyword(os.path.join(TEST_DIR, filename))
    elapsed = time.perf_counter() - start
    times.append(elapsed)
    ok = matched == expected
    correct += ok
    print(f"{filename:<28}{expected:<14}{str(matched):<14}{elapsed:<10.2f}{'PASS' if ok else 'FAIL'}")

total = len(test_files)
print()
print(f"Accuracy:        {correct} of {total} ({100 * correct / total:.0f}%)")
print(f"Processing time: average {sum(times) / total:.2f} s, slowest {max(times):.2f} s")