import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
TOKEN_MINT = "4fJVpHzgaQ5F5BmFWpLrVf7zdmkYJccgcz6XMQo1pump"  # Mint za Introvert

@app.route("/", methods=["POST"])
def handle_webhook():
    data = request.get_json()
    print("📥 Stigao payload:", data)

    if not data:
        return jsonify({"error": "No data"}), 400

    for tx in data:
        signature = tx.get("transaction", {}).get("signatures", [None])[0]
        post_balances = tx.get("meta", {}).get("postTokenBalances", [])
        pre_balances = tx.get("meta", {}).get("preTokenBalances", [])

        if not signature or not post_balances or not pre_balances:
            continue

        # Tražimo stanje za mint koji nas zanima
        introvert_pre = next((b for b in pre_balances if b["mint"] == TOKEN_MINT), None)
        introvert_post = next((b for b in post_balances if b["mint"] == TOKEN_MINT), None)

        if not introvert_pre or not introvert_post:
            continue

        pre_amount = float(introvert_pre["uiTokenAmount"]["uiAmount"])
        post_amount = float(introvert_post["uiTokenAmount"]["uiAmount"])
        delta = round(abs(post_amount - pre_amount), 2)

        if delta < 50000:
            continue  # preskoči transakcije manje od $50000

        tx_type = "Kupovina" if post_amount > pre_amount else "Prodaja"

        message = (
            f"📢 Nova transakcija!\n\n"
            f"Tip: {tx_type}\n"
            f"Iznos: ${delta:.2f}\n"
            f"Signature: {signature}"
        )

        send_telegram_message(message)

    return "OK", 200

def send_telegram_message(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("TELEGRAM_CHAT_ID ili TOKEN nije postavljen.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    response = requests.post(url, json=payload)

    print("📨 Telegram response:", response.status_code, response.text)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)


















