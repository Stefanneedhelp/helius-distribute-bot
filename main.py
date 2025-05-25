from flask import Flask, request
import os
import requests

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

TOKEN_PRICE = 0.012  # cena tokena u USDC

@app.route("/", methods=["POST"])
def helius_webhook():
    try:
        data_list = request.get_json()
        print("Primljeno:", data_list)

        for data in data_list:
            transfers = data.get("events", {}).get("tokenTransfers", [])
            print("Transferi pronađeni:", transfers)

            if not transfers:
                continue

            for transfer in transfers:
                amount = float(transfer["tokenAmount"]["amount"])
                sender = transfer["from"]
                receiver = transfer["to"]
                usd_value = amount * TOKEN_PRICE

                print(f"Obrađujem transfer: {amount} tokena (~${usd_value:.2f})")

                if usd_value < 20:
                    print(f"Ignorisano jer je manje od $20")
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
    print("Šaljem poruku na Telegram:", text)
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    print("Telegram odgovor:", response.status_code, response.text)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)





