import os
from dotenv import load_dotenv

load_dotenv()  # loads from .env file locally; on Render uses environment variables

API_ID   = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
