from flask import Flask, request
import os
import requests

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Cena 1 Distribute.AI tokena u USDC (postavi stvarnu ako znaš)
TOKEN_PRICE = 0.012  # ← Ovde menjaš po potrebi

@app.route("/", methods=["POST"])
def helius_webhook():
    data = request.get_json()

    try:
        tx = data["transactions"][0]
        transfer = tx["tokenTransfers"][0]
        signature = tx["signature"]

        # Detalji o transferu
        amount = float(transfer["rawTokenAmount"]["tokenAmount"])
        sender = transfer["fromUserAccount"]
        receiver = transfer["toUserAccount"]

        # Preračunavanje vrednosti u USD
        usd_value = amount * TOKEN_PRICE

        # Ako je vrednost manja od $5,000 → ignoriši
        if usd_value < 5000:
            print(f"Ignorisano: ${usd_value:.2f}")
            return {"status": "ignored - below threshold"}

        # Sastavi poruku
        message = (
            f"*💸 Velika transakcija DISTRIBUTE.AI!*\n"
            f"Iznos: `{int(amount)}` (~${usd_value:,.2f})\n"
            f"Od: `{sender}`\n"
            f"Ka: `{receiver}`\n"
            f"[Pogledaj na Solscan](https://solscan.io/tx/{signature})"
        )

        send_telegram_message(message)

    except Exception as e:
        print(f"Greška u obradi: {e}")
        return {"status": "error"}, 500

    return {"status": "ok"}

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

