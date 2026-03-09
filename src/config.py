import os
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "1221")
DB_NAME = os.getenv("DB_NAME", "shortener")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "5370")
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}"

SECRET = os.getenv("SECRET", "secret-key")

# import os, base64
# print(base64.urlsafe_b64encode(os.urandom(32)).decode())