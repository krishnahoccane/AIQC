import os
import time
import hmac
import hashlib
import base64
import requests


class ACRYouTubeMatcher:

    def __init__(self):
        self.host = os.getenv("ACR_HOST")
        self.access_key = os.getenv("ACR_ACCESS_KEY")
        self.access_secret = os.getenv("ACR_ACCESS_SECRET")
        self.endpoint = f"https://{self.host}/v1/identify"

    def _sign(self, string_to_sign):

        return base64.b64encode(
            hmac.new(
                self.access_secret.encode(),
                string_to_sign.encode(),
                digestmod=hashlib.sha1
            ).digest()
        ).decode()

    def recognize_audio(self, file_path):

        http_method = "POST"
        http_uri = "/v1/identify"
        data_type = "audio"
        signature_version = "1"
        timestamp = str(int(time.time()))

        string_to_sign = "\n".join([
            http_method,
            http_uri,
            self.access_key,
            data_type,
            signature_version,
            timestamp
        ])

        signature = self._sign(string_to_sign)

        files = {
            "sample": open(file_path, "rb")
        }

        data = {
            "access_key": self.access_key,
            "data_type": data_type,
            "signature_version": signature_version,
            "signature": signature,
            "sample_bytes": os.path.getsize(file_path),
            "timestamp": timestamp
        }

        response = requests.post(self.endpoint, files=files, data=data)

        return response.json()
    def parse_youtube_match(self, acr_response):

        try:
            music = acr_response["metadata"]["music"][0]
            yt = music["external_metadata"]["youtube"]

            return {
                "title": music["title"],
                "artist": music["artists"][0]["name"],
                "youtube_url": f"https://youtube.com/watch?v={yt['vid']}"
            }

        except:
            return None
    
    def parse_spotify_match(self, acr_response):

        try:
            music = acr_response["metadata"]["music"][0]
            spotify = music["external_metadata"]["spotify"]

            return {
                "title": music["title"],
                "artist": music["artists"][0]["name"],
                "spotify_id": spotify["track"]["id"],
                "spotify_url": f"https://open.spotify.com/track/{spotify['track']['id']}"
            }

        except:
            return None