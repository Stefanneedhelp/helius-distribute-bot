import os
from flask import Flask, request
import requests
from dotenv import load_dotenv

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
            price_usd = float(data["pairs"][0]["priceUsd"])
            return price_usd
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
    print(f"📥 Stigao payload: {payload}")

    for tx in payload:
        logs = tx.get("meta", {}).get("logMessages", [])
        if not any("Instruction: Swap" in log for log in logs):
            print("⏩ Preskačem: nije swap.")
            continue

        post_balances = tx.get("meta", {}).get("postTokenBalances", [])
        pre_balances = tx.get("meta", {}).get("preTokenBalances", [])

        for post in post_balances:
            if post.get("mint") != MONITORED_MINT:
                continue

            owner = post.get("owner")
            decimals = int(post["uiTokenAmount"]["decimals"])
            post_amount = int(post["uiTokenAmount"]["amount"])

            # Nađi pre amount za istog ownera
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
            print(f"📊 {direction} {delta:.4f} × ${usd_price:.4f} = ${value_usd:.2f}")

            if value_usd >= 100:
                msg = (
                    f"🔁 <b>{direction} ${value_usd:,.2f}</b>\n"
                    f"{tx.get('blockTime', '')}"
                )
                send_telegram_message(msg)
            else:
                print(f"⏬ Preskačem ispod $100: {value_usd}")

    return "OK", 200

if __name__ == "__main__":
    app.run(debug=True)














