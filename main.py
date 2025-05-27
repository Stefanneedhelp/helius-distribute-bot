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

def get_token_price(mint):
    try:
        res = requests.get(DEXSCREENER_API + mint)
        data = res.json()
        return float(data["pairs"][0]["priceUsd"])
    except Exception as e:
        print(f"Greška pri dohvatanju cene za {mint}: {e}")
        return 0

def is_swap(logs):
    return any("Swap" in log for log in logs)

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
            amount = token.get("uiTokenAmount", {}).get("uiAmount", 0)

            if mint and amount:
                price = get_token_price(mint)
                usd_value = amount * price

                if usd_value < MIN_USD:
                    print(f"Preskačem ispod $100: {usd_value}")
                    continue

                timestamp = datetime.utcfromtimestamp(tx["blockTime"]).strftime("%Y-%m-%d %H:%M:%S UTC")
                message = f"✅ SWAP ${usd_value:,.2f}\n{timestamp}"

                asyncio.run(bot.send_message(chat_id=CHAT_ID, text=message))
                print("✅ Šaljem poruku:", message)
                break

    except Exception as e:
        print("❌ Greška:", e)

    return "OK"


















