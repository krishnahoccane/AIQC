import os
import time

UPLOAD_DIR = "uploads"
EXPIRATION_SECONDS = 3 * 24 * 60 * 60  # 3 days


def cleanup_old_files():
    now = time.time()

    if not os.path.exists(UPLOAD_DIR):
        return

    for filename in os.listdir(UPLOAD_DIR):
        file_path = os.path.join(UPLOAD_DIR, filename)

        if os.path.isfile(file_path):
            file_age = now - os.path.getmtime(file_path)

            if file_age > EXPIRATION_SECONDS:
                os.remove(file_path)
