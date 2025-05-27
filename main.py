import os
import requests
import telegram
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
DEXSCREENER_API = "https://api.dexscreener.com/latest/dex/tokens/"
MONITORED_MINT = os.getenv("MONITORED_MINT")

bot = telegram.Bot(token=BOT_TOKEN)

def get_token_price(mint_address):
    try:
        response = requests.get(DEXSCREENER_API + mint_address)
        data = response.json()
        price = float(data["pairs"][0]["priceUsd"])
        return price
    except Exception as e:
        print(f"[DEX Screener] Greška: {e}")
        return None

@app.route("/", methods=["POST"])
def webhook():
    print("✅ Webhook primljen.")
    try:
        payload = request.json
        print("📥 Stigao payload:", payload)

        for tx in payload:
            instructions = tx.get("meta", {}).get("logMessages", [])
            if not any("Instruction: Swap" in msg for msg in instructions):
                print("⛔ Preskačem jer nije SWAP transakcija")
                continue

            post_token_balances = tx.get("meta", {}).get("postTokenBalances", [])
            mint_addresses = [b.get("mint") for b in post_token_balances if b.get("mint")]

            if MONITORED_MINT not in mint_addresses:
                print("⛔ Preskačem jer nema traženog mint-a")
                continue

            price = get_token_price(MONITORED_MINT)
            if not price:
                print("⛔ Preskačem jer nema cene sa DEX Screenera")
                continue

            amount_raw = max([
                int(b["uiTokenAmount"]["amount"])
                for b in post_token_balances
                if b.get("mint") == MONITORED_MINT
            ], default=0)

            decimals = next((int(b["uiTokenAmount"]["decimals"]) for b in post_token_balances if b.get("mint") == MONITORED_MINT), 9)
            amount = amount_raw / (10 ** decimals)
            usd_value = amount * price

            if usd_value < 100:
                print(f"⛔ Preskačem ispod $100: {usd_value:.2f}")
                continue

            timestamp = datetime.utcfromtimestamp(tx["blockTime"]).strftime("%Y-%m-%d %H:%M:%S UTC")
            tx_type = "BUY" if any("Instruction: Buy" in msg for msg in instructions) else (
                      "SELL" if any("Instruction: Sell" in msg for msg in instructions) else "SWAP")

            message = f"{tx_type} ${usd_value:.2f}\n{timestamp}"
            print("✅ Šaljem poruku:", message)
            bot.send_message(chat_id=CHAT_ID, text=message)

    except Exception as e:
        print("Greška u obradi webhook-a:", e)
    return "OK", 200

if __name__ == "__main__":
    app.run(debug=True)





















