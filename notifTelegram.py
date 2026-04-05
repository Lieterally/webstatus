import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

BOT_TOKEN = f'{TELEGRAM_BOT_TOKEN}'
# CHAT_ID = f'{TELEGRAM_CHAT_ID}'


def notifTelegram(chat_ids, description, list_web):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    message = f"*Informasi | Status Website*\n\nHalo Tim ICT ITK..\nBerikut status terbaru untuk daftar website anda:\n\n{description}\n\n{list_web}"

    for chat_id in chat_ids:

        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }

        response = requests.post(url, json=payload)
        print("Telegram response:", response.status_code, response.text)

# notifTelegram(BOT_TOKEN, CHAT_ID, "Website CE ITK", "❌ DOWN")
