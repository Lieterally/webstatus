import requests
import time
from config import TELEGRAM_BOT_TOKEN
from models import db, TelegramTarget
from app import app

BOT_TOKEN = f'{TELEGRAM_BOT_TOKEN}'
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


commands = [
    {"command": "chat_id", "description": "Get your chat ID"},
    {"command": "help", "description": "Show available commands"},
    {"command": "start", "description": "Start the bot"}
]

requests.post(f"{BASE_URL}/setMyCommands", json={"commands": commands})

last_update_id = None

while True:
    url = f"{BASE_URL}/getUpdates"
    if last_update_id:
        url += f"?offset={last_update_id + 1}"

    res = requests.get(url).json()

    for update in res.get("result", []):
        last_update_id = update["update_id"]

        message = update.get("message", {})
        text = message.get("text", "")
        chat_id = message.get("chat", {}).get("id")

        if not text or not chat_id:
            continue

        # 🔥 COMMAND HANDLER
        if text == "/chat_id":
            reply = f"📌 Your chat ID is:\n{chat_id}"

        elif text == "/help":
            reply = (
                "Bot Commands\n\n"
                "/chat\\_id"
            )

            print(f"Received /help command from chat_id: {chat_id}")

        elif text == "/start":
            reply = (
                "Halo 👋\n\n"
                "Gunakan /help untuk melihat daftar perintah."
            )
            print(f"Received /start command from chat_id: {chat_id}")

        elif text == "/unsubscribe":
            with app.app_context():
                target = TelegramTarget.query.filter_by(
                    chat_id=str(chat_id)).first()

                if target:
                    if not target.is_active:
                        reply = "⚠️ Kamu sudah dalam status tidak aktif."
                    else:
                        target.is_active = False
                        db.session.commit()
                        reply = "❌ Berhasil unsubscribe dari notifikasi."
                else:
                    reply = "⚠️ Kamu belum terdaftar. Gunakan /recipient dulu."

        else:
            reply = "❓ Perintah tidak dikenal. Gunakan /help."

        # ✅ Send response
        requests.post(f"{BASE_URL}/sendMessage", json={
            "chat_id": chat_id,
            "text": reply,
            "parse_mode": "Markdown"
        })

    time.sleep(1)
