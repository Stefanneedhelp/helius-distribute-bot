import os
import requests
import asyncio
from datetime import datetime
from flask import Flask, request
from telegram import Bot

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
DEXSCREENER_API = "https://api.dexscreener.com/latest/dex/tokens/"
MINT_ADDRESS = "2AEU9yWk3dEGnVwRaKv4div5TarC4dn7axFLyz6zG4Pf"

bot = Bot(token=BOT_TOKEN)


def extract_mint_and_type(data):
    try:
        tx = data[0]
        token_balances = tx["meta"].get("postTokenBalances", [])
        for balance in token_balances:
            if balance.get("mint") == MINT_ADDRESS:
                return MINT_ADDRESS, "SWAP"
    except Exception as e:
        print(f"Greška u extract_mint_and_type: {e}")
    return None, None


def fetch_price_usd(mint_address):
    try:
        response = requests.get(DEXSCREENER_API + mint_address)
        response.raise_for_status()
        data = response.json()
        price = float(data["pairs"][0]["priceUsd"])
        return price
    except Exception as e:
        print(f"Greška kod dobijanja cene: {e}")
        return None


@app.route("/", methods=["POST"])
def handle_webhook():
    payload = request.get_json()
    print("✅ Webhook primljen.")

    try:
        mint, tx_type = extract_mint_and_type(payload)
        if not mint:
            print("⛔ Nema mint adrese, preskačem.")
            return "OK"

        price_usd = fetch_price_usd(mint)
        if not price_usd:
            print("⛔ Nema cene za token.")
            return "OK"

        # Procenjena vrednost u USD (pojednostavljeno – koristiš 1 token po transakciji za primer)
        amount_usd = price_usd * 1  # Prava logika može da koristi količinu iz postTokenBalances

        if amount_usd < 100:
            print(f"Preskačem ispod $100: {amount_usd}")
            return "OK"

        message = f"✅ {tx_type} ${amount_usd:,.2f}\n{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        asyncio.run(bot.send_message(chat_id=CHAT_ID, text=message))
        print("✅ Poruka poslata.")
    except Exception as e:
        print(f"❌ Greška u webhook handleru: {e}")

    return "OK"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)


















