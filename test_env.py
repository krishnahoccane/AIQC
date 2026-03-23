import os
from dotenv import load_dotenv

# 1. This magically finds your .env file and loads ALL the variables at once
load_dotenv()

# 2. Grab the variables
host = os.getenv("ACR_HOST")
key = os.getenv("ACR_ACCESS_KEY")
secret = os.getenv("ACR_ACCESS_SECRET")

# 3. Print them out to verify (masking the secret for safety)
print(f"Host: {host}")
print(f"Access Key: {key}")

if secret:
    print(f"Secret Key: Loaded successfully! (Starts with {secret[:4]}...)")
else:
    print("Secret Key: None")