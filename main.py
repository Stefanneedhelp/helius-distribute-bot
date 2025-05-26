import os
import json
import requests
from flask import Flask, request

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
DEXSCREENER_API = "https://api.dexscreener.com/latest/dex/tokens/"
MONITORED_MINT = os.getenv("MONITORED_MINT")  # opciono

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Greška pri slanju poruke: {e}")

def get_token_price(mint_address):
    try:
        response = requests.get(DEXSCREENER_API + mint_address)
        data = response.json()
        if "pairs" in data and len(data["pairs"]) > 0:
            return float(data["pairs"][0]["priceUsd"])
    except Exception as e:
        print(f"Greška kod preuzimanja cene: {e}")
    return None

@app.route("/", methods=["POST"])
def webhook():
    data = request.json
    print("📥 Stigao payload:", json.dumps(data, indent=2))

    try:
        token_balances = data[0]["meta"]["postTokenBalances"]
        mint_addresses = list({t["mint"] for t in token_balances})
    except Exception as e:
        print(f"Ne mogu da izvucem mint adrese: {e}")
        return "OK"

    for mint in mint_addresses:
        if MONITORED_MINT and mint != MONITORED_MINT:
            continue

        price = get_token_price(mint)
        if price is None:
            print("Greška kod preuzimanja cene sa DexScreener-a.")
            continue

        if price < 1:
            print(f"Preskačem token ispod $1: {price}")
            continue

        msg = f"📈 Detektovana transakcija za token:\nMint: {mint}\nCena: ${price:.4f}"
        send_message(msg)

    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)

















