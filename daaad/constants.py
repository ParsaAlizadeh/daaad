import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise Exception("TOKEN is empty")

DEBUG = os.getenv("DEBUG", "true")
DEBUG = DEBUG.lower() == "true"
