import os
from flask import Flask, request
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
DEXSCREENER_API = "https://api.dexscreener.com/latest/dex/tokens/"
MONITORED_MINT = os.getenv("MONITORED_MINT")

def get_token_price(mint_address):
    try:
        url = f"{DEXSCREENER_API}{mint_address}"
        response = requests.get(url)
        data = response.json()
        if "pairs" in data and len(data["pairs"]) > 0:
            return float(data["pairs"][0]["priceUsd"])
    except Exception as e:
        print(f"❌ Greška u dohvatanju cene: {e}")
    return None

def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
        response = requests.post(url, json=payload)
        print(f"✅ Poslata poruka: {response.status_code}")
    except Exception as e:
        print(f"❌ Greška u slanju poruke: {e}")

@app.route("/", methods=["POST"])
def webhook():
    payload = request.json
    print("✅ Webhook primljen.")

    for tx in payload:
        logs = tx.get("meta", {}).get("logMessages", [])
        if not any("Instruction: Swap" in log for log in logs):
            print("⏩ Preskačem: nije swap.")
            continue

        post_balances = tx.get("meta", {}).get("postTokenBalances", [])
        pre_balances = tx.get("meta", {}).get("preTokenBalances", [])
        timestamp = tx.get("blockTime", 0)
        time_str = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S UTC")

        for post in post_balances:
            if post.get("mint") != MONITORED_MINT:
                continue

            owner = post.get("owner")
            decimals = int(post["uiTokenAmount"]["decimals"])
            post_amount = int(post["uiTokenAmount"]["amount"])

            # Traži prethodno stanje za istog vlasnika
            pre_amount = 0
            for pre in pre_balances:
                if pre.get("mint") == MONITORED_MINT and pre.get("owner") == owner:
                    pre_amount = int(pre["uiTokenAmount"]["amount"])
                    break

            delta_raw = post_amount - pre_amount
            delta = abs(delta_raw) / (10 ** decimals)
            usd_price = get_token_price(MONITORED_MINT)

            if usd_price is None:
                print("❌ Nema cene.")
                continue

            value_usd = delta * usd_price
            direction = "BUY" if delta_raw > 0 else "SELL"

            if value_usd >= 1000:
                msg = (
                    f"🔁 <b>{direction} ${value_usd:,.2f}</b>\n"
                    f"<b>Adresa:</b> <code>{owner}</code>\n"
                    f"<b>Vreme:</b> {time_str}"
                )
                send_telegram_message(msg)
            else:
                print(f"⏬ Preskačem ispod $100: {value_usd:.2f}")

    return "OK", 200

if __name__ == "__main__":
    app.run(debug=True)














