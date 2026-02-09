import sys
import json
import essentia.standard as es
from spleeter.separator import Separator

import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import logging
logging.getLogger().setLevel(logging.ERROR)


def process_audio(file_path):
    loader = es.MonoLoader(filename=file_path)
    audio = loader()

    key_extractor = es.KeyExtractor()
    key, scale, strength = key_extractor(audio)

    separator = Separator('spleeter:2stems')
    separator.separate_to_file(file_path, 'output')

    return {
        "key": key,
        "scale": scale,
        "confidence": float(strength)
    }


if __name__ == "__main__":
    file_path = sys.argv[1]
    result = process_audio(file_path)
    print(json.dumps(result))
