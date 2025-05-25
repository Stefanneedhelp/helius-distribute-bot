import os
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

@app.route("/", methods=["POST"])
def handle_webhook():
    try:
        payload = request.get_json()

        # Helius šalje listu transakcija
        for tx in payload:
            signature = tx.get("signature", "n/a")
            timestamp = tx.get("timestamp", "n/a")
            description = tx.get("description", "No description")
            type_ = tx.get("type", "Unknown")

            message = f"📥 Nova transakcija:\n🧾 {description}\n📌 Tip: {type_}\n🕒 Vreme: {timestamp}\n🔗 https://solscan.io/tx/{signature}"
            send_telegram_message(message)

        return "OK", 200

    except Exception as e:
        print(f"Webhook error: {e}")
        return "ERROR", 500


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text}
    try:
        response = requests.post(url, json=data)
        if not response.ok:
            print("Telegram error:", response.text)
    except Exception as e:
        print("Telegram exception:", e)

if __name__ == "__main__":
    app.run(debug=True)





