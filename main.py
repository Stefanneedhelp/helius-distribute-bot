import os
import requests
import asyncio
from flask import Flask, request
from telegram import Bot
from datetime import datetime

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
DEXSCREENER_API = "https://api.dexscreener.com/latest/dex/tokens/"
MONITORED_MINT = os.getenv("MONITORED_MINT")

bot = Bot(token=BOT_TOKEN)

@app.route("/", methods=["POST"])
def webhook():
    print("✅ Webhook primljen.")
    data = request.get_json()

    if not data or not isinstance(data, list):
        return "Invalid payload", 400

    for tx in data:
        tx_data = tx.get("meta", {})
        token_balances = tx_data.get("postTokenBalances", [])
        tx_type = None

        for balance in token_balances:
            if balance.get("mint") == MONITORED_MINT:
                amount = int(balance["uiTokenAmount"]["amount"])
                decimals = int(balance["uiTokenAmount"]["decimals"])
                ui_amount = amount / (10 ** decimals)
                if ui_amount < 0.01:
                    continue  # preskoči beznačajne

                # Get USD price
                response = requests.get(DEXSCREENER_API + MONITORED_MINT)
                price = 0
                if response.ok:
                    try:
                        price = float(response.json()["pairs"][0]["priceUsd"])
                    except (KeyError, IndexError, ValueError):
                        pass

                total_value = ui_amount * price
                if total_value < 100:
                    print(f"Preskačem token ispod $100: {total_value}")
                    continue

                # Detekcija tipa transakcije (samo SWAP)
                logs = tx_data.get("logMessages", [])
                tx_type = "SWAP" if any("Instruction: Swap" in msg for msg in logs) else None

                if tx_type:
                    timestamp = datetime.utcfromtimestamp(tx["blockTime"]).strftime('%Y-%m-%d %H:%M:%S UTC')
                    message = f"✅ {tx_type} ${total_value:,.2f}\n{timestamp}"
                    print(message)
                    asyncio.run(bot.send_message(chat_id=CHAT_ID, text=message))

    return "OK"




















