
from flask import Flask, request
import os
import requests

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

TOKEN_PRICE = 0.012  # cena tokena u USDC

@app.route("/", methods=["POST"])
def helius_webhook():
    data = request.get_json()
    print(data)  # <--- ovo dodaj samo za debug

    try:
        # Raw webhook: "events" je u root, "tokenTransfers" je lista
        transfers = data.get("events", {}).get("tokenTransfers", [])

        if not transfers:
            return {"status": "no token transfers"}

        for transfer in transfers:
            amount = float(transfer["tokenAmount"]["amount"])
            sender = transfer["from"]
            receiver = transfer["to"]
            usd_value = amount * TOKEN_PRICE

            if usd_value < 20:
                print(f"Ignorisano: ${usd_value:.2f}")
                continue

            signature = data.get("transaction", {}).get("signature", "N/A")

            msg = (
                f"*💸 Velika transakcija DISTRIBUTE.AI!*\n"
                f"Iznos: `{int(amount)}` (~${usd_value:,.2f})\n"
                f"Od: `{sender}`\n"
                f"Ka: `{receiver}`\n"
                f"[Solscan](https://solscan.io/tx/{signature})"
            )

            send_telegram_message(msg)

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


