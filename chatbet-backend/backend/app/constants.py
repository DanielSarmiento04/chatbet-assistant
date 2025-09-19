import os

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", None)

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable not set")

os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY