import os
import requests
from flask import Flask, request
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
MONITORED_MINT = os.getenv("MONITORED_MINT")

app = Flask(__name__)

def get_token_price(mint_address):
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{mint_address}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if "pairs" in data and len(data["pairs"]) > 0:
            return float(data["pairs"][0]["priceUsd"])
    except Exception as e:
        print(f"Greska kod preuzimanja cene tokena: {e}")
    return None

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Greska kod slanja poruke na Telegram: {e}")

@app.route("/", methods=["POST"])
def handle_webhook():
    data = request.get_json()
    print(f"📥 Stigao payload: {data}")

    token_balances = data[0].get("meta", {}).get("postTokenBalances", [])
    mint_addresses = [t.get("mint") for t in token_balances]

    if MONITORED_MINT in mint_addresses:
        token_info = next((t for t in token_balances if t.get("mint") == MONITORED_MINT), None)
        if token_info:
            amount_raw = int(token_info["uiTokenAmount"]["amount"])
            decimals = int(token_info["uiTokenAmount"]["decimals"])
            amount = amount_raw / (10 ** decimals)

            price = get_token_price(MONITORED_MINT)
            if price is None:
                print("Greska kod preuzimanja cene.")
                return "", 200

            total_value = amount * price
            if total_value < 1:
                print(f"Preskacem transakciju ispod $1: {total_value}")
                return "", 200

            timestamp = data[0].get("blockTime")
            if timestamp:
                dt = datetime.utcfromtimestamp(timestamp)
                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                formatted_time = "Nepoznat"

            msg = (
                f"📡 <b>Nova transakcija!</b>\n\n"
                f"🪙 <b>Token:</b> <code>{MONITORED_MINT}</code>\n"
                f"💰 <b>Iznos:</b> {amount:.4f}\n"
                f"💵 <b>Vrednost:</b> ${total_value:.2f}\n"
                f"🕒 <b>Vreme:</b> {formatted_time} UTC"
            )
            send_telegram_message(msg)

    return "", 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)

















