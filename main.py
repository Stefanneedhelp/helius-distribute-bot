
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
        meta = tx.get("meta", {})
        block_time = tx.get("blockTime")
        log_messages = meta.get("logMessages", [])
        pre_balances = meta.get("preTokenBalances", [])
        post_balances = meta.get("postTokenBalances", [])

        amount_changed = None

        for pre, post in zip(pre_balances, post_balances):
            if pre["mint"] == MONITORED_MINT and post["mint"] == MONITORED_MINT:
                try:
                    pre_amount = int(pre["uiTokenAmount"]["amount"])
                    post_amount = int(post["uiTokenAmount"]["amount"])
                    decimals = int(post["uiTokenAmount"]["decimals"])
                except:
                    continue

                delta = abs(post_amount - pre_amount)
                if delta == 0:
                    continue
                amount_changed = delta / (10 ** decimals)
                break  # uzmi samo prvu promenjenu vrednost

        if not amount_changed:
            print("Nema promena u količini tokena.")
            continue

        # Cena sa DexScreener-a
        price_usd = 0
        try:
            res = requests.get(DEXSCREENER_API + MONITORED_MINT)
            res.raise_for_status()
            price_usd = float(res.json()["pairs"][0]["priceUsd"])
        except:
            print("Greska pri dohvatanju cene.")
            continue

        total_value = amount_changed * price_usd
        if total_value < 100:
            print(f"Preskačem ispod $100: {total_value}")
            continue

        # Tip transakcije
        tx_type = "SWAP" if any("Instruction: Swap" in log for log in log_messages) else "TX"

        # Vremenska oznaka
        timestamp = datetime.utcfromtimestamp(block_time).strftime('%Y-%m-%d %H:%M:%S UTC')
        message = f"✅ {tx_type} ${total_value:,.2f}\n{timestamp}"
        print(message)
        asyncio.run(bot.send_message(chat_id=CHAT_ID, text=message))

    return "OK"



















