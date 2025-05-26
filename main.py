
from flask import Flask, request
import os
import requests

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
MONITORED_MINT = "2AEU9yWk3dEGnVwRaKv4div5TarC4dn7axFLyz6zG4Pf"

@app.route("/", methods=["POST"])
def handle_webhook():
    data = request.json
    if not data:
        return "No data", 400

    print("📥 Stigao payload:", data)

    for tx in data:
        try:
            token_balance_changes = tx["meta"].get("postTokenBalances", [])
            instructions = tx["meta"].get("logMessages", [])

            # Pronađi promenu balansa za posmatrani token
            for balance in token_balance_changes:
                if balance["mint"] == MONITORED_MINT:
                    ui_amount = float(balance["uiTokenAmount"]["uiAmount"])
                    if ui_amount is None or ui_amount < 0.01:
                        continue  # ignoriši male transakcije

                    # Transakcije ispod 100 USD ignoriši
                    if ui_amount < 100:
                        continue

                    # Odredi tip transakcije
                    tx_type = "Kupovina" if "Instruction: Buy" in str(instructions) else "Prodaja" if "Instruction: Sell" in str(instructions) else "Transfer"

                    # Pošalji poruku
                    signature = tx["transaction"]["signatures"][0]
                    message = (
                        f"📢 Nova transakcija!\n\n"
                        f"Tip: {tx_type}\n"
                        f"Iznos: {ui_amount:.2f} USD\n"
                        f"Signature: {signature}"
                    )
                    send_telegram_message(message)
        except Exception as e:
            print("Greška:", e)

    return "OK", 200

def send_telegram_message(message):
    if not BOT_TOKEN or not CHAT_ID:
        print("BOT_TOKEN ili CHAT_ID nisu postavljeni.")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    response = requests.post(url, json=payload)
    print("📨 Telegram response:", response.status_code, response.text)

if __name__ == "__main__":
    app.run(debug=True)


















