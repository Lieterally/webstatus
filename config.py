# config.py
import os
from pathlib import Path


try:
    from dotenv import load_dotenv  # pip install python-dotenv
    # Load .env if present (local dev); in prod (Render/GitHub Actions) real env is used
    load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")
except Exception:
    pass

def require(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return v

SECRET_KEY = require("SECRET_KEY")
SQLALCHEMY_DATABASE_URI = require("DATABASE_URL")
SQLALCHEMY_TRACK_MODIFICATIONS = False

PHONE_NUM = require("PHONE_NUM")
TELEGRAM_BOT_TOKEN = require("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = require("TELEGRAM_CHAT_ID")
OCATELKOM_BEARER   = require("OCATELKOM_BEARER")
OCATELKOM_ENDPOINT = require("OCATELKOM_ENDPOINT")