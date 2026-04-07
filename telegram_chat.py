def run_telegram_bot():

    import requests
    import time
    from config import TELEGRAM_BOT_TOKEN
    from models import db, TelegramTarget
    from app import app

    BOT_TOKEN = f'{TELEGRAM_BOT_TOKEN}'
    BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


    commands = [
        {"command": "start", "description": "Start the bot"},
        {"command": "help", "description": "Show available commands"},
        {"command": "chat_id", "description": "Get your chat ID"},
        {"command": "recipient", "description": "Register as a notification recipient"},
        {"command": "unsubscribe", "description": "Unsubscribe from notifications"},
        {"command": "subscribe", "description": "Subscribe to notifications"}
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

            elif text == "/subscribe":
                with app.app_context():
                    target = TelegramTarget.query.filter_by(
                        chat_id=str(chat_id)).first()

                    if target:
                        if target.is_active:
                            reply = "⚠️ Kamu sudah dalam status aktif."
                        else:
                            target.is_active = True
                            db.session.commit()
                            reply = "✅ Berhasil subscribe ke notifikasi."
                    else:
                        reply = "⚠️ Kamu belum terdaftar. Gunakan /recipient dulu."

            elif text == "/recipient":
                with app.app_context():
                    target = TelegramTarget.query.filter_by(
                        chat_id=str(chat_id)).first()

                    if target:
                        if target.is_active:
                            reply = "⚠️ Kamu sudah terdaftar dan aktif menerima notifikasi."
                        else:
                            target.is_active = True
                            db.session.commit()
                            reply = "✅ Kamu berhasil diaktifkan kembali sebagai penerima notifikasi."
                    else:
                        new_target = TelegramTarget(
                            chat_id=str(chat_id),
                            is_active=True
                        )
                        db.session.add(new_target)
                        db.session.commit()

                        reply = "✅ Kamu berhasil terdaftar sebagai penerima notifikasi."

            else:
                reply = "❓ Perintah tidak dikenal. Gunakan /help."

            requests.post(f"{BASE_URL}/sendMessage", json={
                "chat_id": chat_id,
                "text": reply,
                "parse_mode": "Markdown"
            })

        time.sleep(1)
