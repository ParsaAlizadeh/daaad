import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise Exception("TOKEN is empty")

APIKEY = os.getenv("APIKEY")
if not APIKEY:
    raise Exception("APIKEY is empty")

DEBUG = os.getenv("DEBUG", "true")
DEBUG = DEBUG.lower() == "true"
