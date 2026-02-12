import os
import librosa
import numpy as np

INPUT_FOLDER = "input_songs"
OUTPUT_FOLDER = "output_results"

def detect_blank_spaces(audio_file, threshold=0.01, min_silence_duration=1.0):
    """
    Detects silent/blank spaces in an audio file.
    Returns list of (start, end) times in seconds.
    """
    try:
        y, sr = librosa.load(audio_file, sr=None)
        amplitude = np.abs(y)
        silence_mask = amplitude < threshold

        silent_sections = []
        start = None
        for i, is_silent in enumerate(silence_mask):
            if is_silent and start is None:
                start = i
            elif not is_silent and start is not None:
                end = i
                duration = (end - start) / sr
                if duration >= min_silence_duration:
                    silent_sections.append((start / sr, end / sr))
                start = None

        return silent_sections
    except Exception as e:
        print(f"  Error while analyzing {audio_file}: {str(e)}")
        return []

def main():
    print("<µ Blank Space Detector started...")

    # Ensure input folder exists
    if not os.path.exists(INPUT_FOLDER):
        print(f"  Input folder not found. Creating one at {INPUT_FOLDER}")
        os.makedirs(INPUT_FOLDER)
        return

    # Ensure output folder exists
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    # Process each audio file
    for file_name in os.listdir(INPUT_FOLDER):
        file_path = os.path.join(INPUT_FOLDER, file_name)

        if not file_path.lower().endswith((".mp3", ".wav", ".flac", ".ogg")):
            print(f"í Skipping non-audio file: {file_name}")
            continue

        print(f"<¶ Processing: {file_name} ...")

        blank_spaces = detect_blank_spaces(file_path)

        if blank_spaces:
            print(f" Blank spaces found in {file_name}:")
            for start, end in blank_spaces:
                print(f"   - From {start:.2f}s to {end:.2f}s")
        else:
            print(f"L No blank spaces detected in {file_name}")

        # Save results into a text file
        try:
            output_file = os.path.join(OUTPUT_FOLDER, f"{os.path.splitext(file_name)[0]}_results.txt")
            with open(output_file, "w", encoding="utf-8") as f:
                if blank_spaces:
                    f.write(f"Blank spaces in {file_name}:\n")
                    for start, end in blank_spaces:
                        f.write(f"- From {start:.2f}s to {end:.2f}s\n")
                else:
                    f.write(f"No blank spaces detected in {file_name}\n")
        except Exception as e:
            print(f"  Could not save results for {file_name}: {str(e)}")

    print(" Processing complete!")

if __name__ == "__main__":
    main()
