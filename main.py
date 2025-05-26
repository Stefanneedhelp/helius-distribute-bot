import os
import requests
import telegram
from flask import Flask, request, Response
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
DEXSCREENER_API = "https://api.dexscreener.com/latest/dex/tokens/"
MONITORED_MINT = os.getenv("MONITORED_MINT")  # nije više obavezno

bot = telegram.Bot(token=BOT_TOKEN)
app = Flask(__name__)

@app.route("/", methods=["POST"])
def webhook():
    payload = request.json
    print(f"📥 Stigao payload: {payload}")

    try:
        tx = payload[0]
        mint_address = MONITORED_MINT or find_mint_address(tx)

        if not mint_address:
            print("⚠️ Nema mint adrese")
            return Response("No mint", status=200)

        token_transfers = extract_token_transfers(tx, mint_address)
        if not token_transfers:
            print("ℹ️ Nema transfera za ovaj token")
            return Response("No relevant transfers", status=200)

        for t in token_transfers:
            amount = t["uiTokenAmount"]["uiAmount"]
            owner = t["owner"]
            if amount is None or amount == 0:
                continue

            # Cena sa DexScreener
            resp = requests.get(f"{DEXSCREENER_API}{mint_address}")
            data = resp.json()
            if not data["pairs"]:
                print("❌ DexScreener nije vratio cenu")
                return Response("No price data", status=200)

            price = float(data["pairs"][0]["priceUsd"])
            usd_value = amount * price
            print(f"[DEBUG] {amount} * ${price:.4f} = ${usd_value:.2f}")

            if usd_value < 100:
                print(f"⛔ Preskačem ispod $100: {usd_value}")
                return Response("Below threshold", status=200)

            tx_type = detect_tx_type(tx)
            timestamp = datetime.utcfromtimestamp(tx["blockTime"]).strftime('%Y-%m-%d %H:%M:%S')
            msg = f"{tx_type.upper()} ${usd_value:,.2f} @ {timestamp} UTC"
            bot.send_message(chat_id=CHAT_ID, text=msg)

    except Exception as e:
        print(f"❌ Greška: {e}")
        return Response("Error", status=500)

    return Response("OK", status=200)

def find_mint_address(tx):
    try:
        for token in tx["meta"]["postTokenBalances"]:
            return token["mint"]
    except Exception:
        pass
    return None

def extract_token_transfers(tx, mint_address):
    try:
        return [
            token for token in tx["meta"]["postTokenBalances"]
            if token["mint"] == mint_address
        ]
    except Exception:
        return []

def detect_tx_type(tx):
    logs = tx["meta"].get("logMessages", [])
    for log in logs:
        if "Instruction: Swap" in log:
            return "swap"
        elif "Instruction: Buy" in log:
            return "buy"
        elif "Instruction: Sell" in log:
            return "sell"
    return "unknown"

app.run(host="0.0.0.0", port=10000)





















