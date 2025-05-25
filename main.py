from flask import Flask, request
import os
import requests

app = Flask(__name__)

# Uzimanje tokena i chat ID-a iz okruženja
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Glavna ruta za Helius webhook
@app.route("/", methods=["POST"])
def helius_webhook():
    data = request.get_json()

    try:
        # Uzimamo prvu transakciju iz liste
        tx = data["transactions"][0]
        transfer = tx["tokenTransfers"][0]
        signature = tx["signature"]

        # Podaci iz transfera
        amount = transfer["rawTokenAmount"]["tokenAmount"]
        sender = transfer["fromUserAccount"]
        receiver = transfer["toUserAccount"]

        # Sastavljanje poruke za Telegram
        message = (
            f"*Nova transakcija DISTRIBUTE.AI*\n"
            f"Iznos: `{amount}`\n"
            f"Od: `{sender}`\n"
            f"Ka: `{receiver}`\n"
            f"[Pogledaj na Solscan](https://solscan.io/tx/{signature})"
        )

        # Slanje poruke
        send_telegram_message(message)

    except Exception as e:
        print("Greška:", e)

    return {"status": "ok"}

# Slanje poruke na Telegram
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

# Pokretanje servera lokalno (za test)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
