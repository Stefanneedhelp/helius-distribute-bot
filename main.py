import os
from flask import Flask, request
import requests

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TOKEN_ADDRESS = "2AEU9yWk3dEGnVwRaKv4div5TarC4dn7axFLyz6zG4Pf"

def send_telegram_message(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Greška: Telegram token ili chat ID nisu postavljeni.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    response = requests.post(url, json=data)
    print(f"📨 Telegram response: {response.status_code} {response.text}")

@app.route("/", methods=["POST"])
def handle_webhook():
    data = request.get_json()
    print(f"📥 Stigao payload: {data}")

    for tx in data:
        try:
            token_transfers = tx["meta"].get("postTokenBalances", [])
            pre_balances = {b["accountIndex"]: b["uiTokenAmount"]["uiAmount"] for b in tx["meta"].get("preTokenBalances", []) if b["mint"] == TOKEN_ADDRESS}
            post_balances = {b["accountIndex"]: b["uiTokenAmount"]["uiAmount"] for b in token_transfers if b["mint"] == TOKEN_ADDRESS}

            for account_index, post_amount in post_balances.items():
                pre_amount = pre_balances.get(account_index, 0)
                delta = post_amount - pre_amount
                if abs(delta) == 0:
                    continue

                # Procena cene po tokenu
                price_per_token = 0.03345  # OVDE ažuriraj ako imaš API ili dinamički izračun
                value_usd = abs(delta) * price_per_token

                if value_usd > 100:
                    action = "Kupovina" if delta > 0 else "Prodaja"
                    signature = tx.get("transaction", {}).get("signatures", ["?"])[0]
                    message = (
                        f"📢 Nova transakcija!\n\n"
                        f"Tip: {action}\n"
                        f"Iznos: ${value_usd:.2f}\n"
                        f"Signature: {signature}"
                    )
                    send_telegram_message(message)

        except Exception as e:
            print(f"Greška u obradi transakcije: {e}")

    return "OK", 200















