# create a quick test file in root
# test_redis.py
from dotenv import load_dotenv
import os
load_dotenv()

url = os.getenv("REDIS_URL")
print(f"REDIS_URL loaded: {url}")

# test direct connection
import redis
try:
    r = redis.from_url(url)
    r.ping()
    print("Redis ping successful!")
except Exception as e:
    print(f"Redis error: {e}")