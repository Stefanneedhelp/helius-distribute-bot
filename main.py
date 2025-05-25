import os
from flask import Flask, request
import requests

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

def send_telegram_message(text):
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    response = requests.post(TELEGRAM_URL, json=payload)
    return response.ok

@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()
    try:
        tx = data["transactions"][0]
        sig = tx["transaction"]["signatures"][0]
        block_time = tx.get("blockTime", "?")
        message = f"\ud83d\udce6 <b>Nova transakcija</b>\n🔗 Signature: <code>{sig}</code>\n🕒 Block time: {block_time}"

        transfers = tx.get("transfers", [])
        if transfers:
            message += "\n💸 Transferi:"
            for tr in transfers:
                message += f"\n- {tr['from']} → {tr['to']}: {tr['amount']} {tr['mint']}"

        send_telegram_message(message)
        return "OK", 200
    except Exception as e:
        print("Webhook error:", e)
        return "Error", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)





