from flask import Flask, request
import requests
import os

app = Flask(__name__)

# 🔐 Telegram token i chat ID iz environmenta
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()
    print("📥 Stigao payload:", data)  # LOG ceo payload

    try:
        # Proveravamo da li je lista (kako Helius obično šalje)
        if isinstance(data, list):
            transaction = data[0]
        else:
            transaction = data

        signature = transaction.get("transaction", {}).get("signatures", [""])[0]

        message = f"📢 Nova transakcija primljena!\n\nSignature: {signature}"
        send_telegram(message)

        return "OK", 200

    except Exception as e:
        print("⚠️ Webhook error:", str(e))
        return "Error", 500

def send_telegram(message):
    payload = {"chat_id": CHAT_ID, "text": message}
    response = requests.post(TELEGRAM_API_URL, json=payload)
    print("📨 Telegram response:", response.status_code, response.text)

if __name__ == "__main__":
    app.run(debug=True)






