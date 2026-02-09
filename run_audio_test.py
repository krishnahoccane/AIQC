from services.audio_analysis import AudioAnalyzer
import pprint

file_path = "sample_data/file_example_MP3_2MG.mp3"

analyzer = AudioAnalyzer(file_path)

try:
    results = analyzer.analyze()
    print("\n=== AUDIO ANALYSIS RESULTS ===\n")
    pprint.pprint(results)

except Exception as e:
    print("Error during analysis:")
    print(e)

    