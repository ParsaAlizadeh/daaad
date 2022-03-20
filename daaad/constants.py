import os
from dotenv import load_dotenv

load_dotenv()

# Bot Config

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise Exception("TOKEN is empty")

APIKEY = os.getenv("APIKEY")
if not APIKEY:
    raise Exception("APIKEY is empty")

DEBUG = os.getenv("DEBUG", "true")
DEBUG = DEBUG.lower() == "true"

CHANNEL = os.getenv("CHANNEL")
if not CHANNEL:
    raise Exception("CHANNEL is empty")
if CHANNEL[0] != '@':
    CHANNEL = int(CHANNEL)

ADMINS = os.getenv("ADMINS", None)
if ADMINS is not None:
    ADMINS = set(map(int, ADMINS.split(':')))
else:
    ADMINS = set()

# Webhook

PORT = os.getenv("PORT", "5000")
PORT = int(PORT)

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
CERT_FILEPATH = os.getenv("CERT_FILEPATH")
