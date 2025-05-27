
import os
from flask import Flask, request
from telegram import Bot
import requests
import asyncio
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
DEX_API = "https://api.dexscreener.com/latest/dex/tokens/"
MIN_USD = 100

app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)

def get_price_usd(mint):
    try:
        r = requests.get(DEX_API + mint)
        data = r.json()
        return float(data["pairs"][0]["priceUsd"])
    except Exception as e:
        print("Greška u dohvatu cene:", e)
        return None

def is_swap(logs):
    return any("Swap" in log for log in logs)

@app.route("/", methods=["POST"])
def webhook():
    data = request.json
    print("✅ Webhook primljen.")
    try:
        tx = data[0]
        logs = tx["meta"].get("logMessages", [])
        if not is_swap(logs):
            print("❌ Nije swap.")
            return "OK"

        token = next((t for t in tx["meta"]["postTokenBalances"] if t.get("mint")), None)
        if not token:
            print("❌ Nema mint adrese.")
            return "OK"

        mint = token["mint"]
        amount = float(token["uiTokenAmount"]["uiAmount"])
        price = get_price_usd(mint)
        if price is None:
            return "OK"

        usd_value = amount * price
        if usd_value < MIN_USD:
            print(f"Preskačem ispod $100: {usd_value}")
            return "OK"

        timestamp = datetime.utcfromtimestamp(tx["blockTime"]).strftime("%Y-%m-%d %H:%M:%S UTC")
        message = f"✅ TX ${usd_value:,.2f}\n{timestamp}"
        asyncio.run(bot.send_message(chat_id=CHAT_ID, text=message))
        print("✅ Poslata poruka:", message)

    except Exception as e:
        print("❌ Greška:", e)

    return "OK"
















