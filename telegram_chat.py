def run_telegram_bot():

    import requests
    import time
    from config import TELEGRAM_BOT_TOKEN
    from models import db, TelegramTarget
    from app import app

    BOT_TOKEN = f'{TELEGRAM_BOT_TOKEN}'
    BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

    try:
        commands = [
            {"command": "start", "description": "Start the bot"},
            {"command": "help", "description": "Show available commands"},
            {"command": "chat_id", "description": "Get your chat ID"},
            {"command": "recipient", "description": "Register as a notification recipient"},
            {"command": "unsubscribe", "description": "Unsubscribe from notifications"},
            {"command": "subscribe", "description": "Subscribe to notifications"}
        ]
        requests.post(f"{BASE_URL}/setMyCommands", json={"commands": commands}, timeout=10)
        print("✅ Telegram commands set")
    except Exception as e:
        print("⚠️ Failed to set commands:", e)

    last_update_id = None

    print("🤖 Telegram bot started...")

    while True:
        try:
            # --- Long polling (WAIT up to 30s for updates) ---
            url = f"{BASE_URL}/getUpdates?timeout=30"
            if last_update_id:
                url += f"&offset={last_update_id + 1}"

            response = requests.get(url, timeout=35)
            data = response.json()

            if not data.get("ok"):
                print("⚠️ Telegram API error:", data)
                time.sleep(5)
                continue

            for update in data.get("result", []):
                last_update_id = update["update_id"]

                message = update.get("message", {})
                text = message.get("text", "")
                chat_id = message.get("chat", {}).get("id")

                username = message.get("from", {}).get("username")
                name = message.get("from", {}).get("first_name", "")

                if not text or not chat_id:
                    continue

                print(f"📩 {chat_id}: {text}")

                # --- COMMAND HANDLING ---
                if text == "/chat_id":
                    reply = f"📌 Your chat ID is:\n{chat_id}"

                elif text == "/help":
                    reply = (
                        "Bot Commands:\n\n"
                        "/chat_id - Get your chat ID\n"
                        "/help - Show available commands\n"
                        "/recipient - Register as notification recipient\n"
                        "/unsubscribe - Stop notifications\n"
                        "/subscribe - Enable notifications"
                    )

                elif text == "/start":
                    reply = "Halo 👋\n\nGunakan /help untuk melihat daftar perintah."

                elif text == "/unsubscribe":
                    with app.app_context():
                        target = TelegramTarget.query.filter_by(chat_id=str(chat_id)).first()

                        if target:
                            if not target.is_active:
                                reply = "⚠️ Kamu sudah tidak aktif."
                            else:
                                target.is_active = False
                                db.session.commit()
                                reply = "❌ Berhasil unsubscribe."
                        else:
                            reply = "⚠️ Kamu belum terdaftar. Gunakan /recipient."

                elif text == "/subscribe":
                    with app.app_context():
                        target = TelegramTarget.query.filter_by(chat_id=str(chat_id)).first()

                        if target:
                            if target.is_active:
                                reply = "⚠️ Kamu sudah aktif."
                            else:
                                target.is_active = True
                                db.session.commit()
                                reply = "✅ Berhasil subscribe."
                        else:
                            reply = "⚠️ Kamu belum terdaftar. Gunakan /recipient."

                elif text == "/recipient":
                    with app.app_context():
                        target = TelegramTarget.query.filter_by(chat_id=str(chat_id)).first()

                        if target:
                            if target.is_active:
                                reply = "⚠️ Kamu sudah terdaftar."
                            else:
                                target.is_active = True
                                db.session.commit()
                                reply = "✅ Kamu diaktifkan kembali."
                        else:
                            new_target = TelegramTarget(
                                chat_id=str(chat_id),
                                name=str(username) if username else str(name),
                                is_active=True
                            )
                            db.session.add(new_target)
                            db.session.commit()
                            reply = "✅ Berhasil terdaftar."

                else:
                    reply = "❓ Perintah tidak dikenal. Gunakan /help."

                # --- SEND RESPONSE (with retry) ---
                try:
                    requests.post(
                        f"{BASE_URL}/sendMessage",
                        json={
                            "chat_id": chat_id,
                            "text": reply
                        },
                        timeout=10
                    )
                except Exception as e:
                    print("❌ Failed to send message:", e)

        except Exception as e:
            print("❌ TELEGRAM BOT CRASH:", e)
            time.sleep(5)
