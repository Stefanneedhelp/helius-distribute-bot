import os
from flask import Flask, request
from telegram import Bot
import requests
import asyncio
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
DEXSCREENER_API = "https://api.dexscreener.com/latest/dex/tokens/"
MIN_USD = 100

app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)

def get_swap_amount_usd(mint_address):
    try:
        response = requests.get(DEXSCREENER_API + mint_address)
        data = response.json()
        price = float(data["pairs"][0]["priceUsd"])
        return price
    except Exception as e:
        print(f"Greška u DexScreener API pozivu: {e}")
        return 0

def is_swap(logs):
    return any("Swap" in msg for msg in logs)

@app.route("/", methods=["POST"])
def webhook():
    payload = request.json
    print("✅ Webhook primljen.")

    try:
        tx = payload[0]
        logs = tx["meta"].get("logMessages", [])
        if not is_swap(logs):
            print("❌ Nije swap transakcija.")
            return "OK"

        token_balances = tx["meta"].get("postTokenBalances", [])
        for token in token_balances:
            mint = token.get("mint")
            if mint:
                usd_value = get_swap_amount_usd(mint)
                if usd_value < MIN_USD:
                    print(f"Preskačem ispod $100: {usd_value}")
                    continue

                timestamp = datetime.utcfromtimestamp(tx["blockTime"]).strftime("%Y-%m-%d %H:%M:%S UTC")
                message = f"✅ SWAP ${usd_value:,.2f}\n{timestamp}"

                asyncio.run(bot.send_message(chat_id=CHAT_ID, text=message))
                print("✅ Šaljem poruku:", message)
                break
    except Exception as e:
        print("❌ Greška u obradi transakcije:", e)

    return "OK"


















