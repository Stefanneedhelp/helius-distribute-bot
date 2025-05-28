import os
from flask import Flask, request
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
DEXSCREENER_API = "https://api.dexscreener.com/latest/dex/tokens/"
MONITORED_MINT = os.getenv("MONITORED_MINT")
SOL_MINT = "So11111111111111111111111111111111111111112"

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
        print(f"✅ Poruka poslata: {response.status_code}")
    except Exception as e:
        print(f"❌ Greška u slanju poruke: {e}")

@app.route("/", methods=["POST"])
def webhook():
    payload = request.json
    print("✅ Webhook primljen.")
    print("DEBUG payload primljen:", payload)

    logs = payload.get("meta", {}).get("logMessages", [])
    if not any("Instruction: Swap" in log for log in logs):
        print("⏩ Preskačeno: nije swap.")
        return "OK", 200

    post_balances = payload.get("meta", {}).get("postTokenBalances", [])
    pre_balances = payload.get("meta", {}).get("preTokenBalances", [])
    block_time = payload.get("blockTime")

    token_delta_map = {}
    sol_delta_map = {}

    for post in post_balances:
        mint = post.get("mint")
        owner = post.get("owner")
        amount = int(post["uiTokenAmount"]["amount"])
        decimals = int(post["uiTokenAmount"]["decimals"])

        for pre in pre_balances:
            if pre.get("mint") == mint and pre.get("owner") == owner:
                pre_amount = int(pre["uiTokenAmount"]["amount"])
                delta = amount - pre_amount
                if mint == MONITORED_MINT:
                    token_delta_map[owner] = {"delta": delta, "decimals": decimals}
                elif mint == SOL_MINT:
                    sol_delta_map[owner] = {"delta": delta, "decimals": decimals}
                break

    for owner in token_delta_map:
        print("🔍 Proveravam vlasnika:", owner)
        if owner in sol_delta_map:
            token_data = token_delta_map[owner]
            sol_data = sol_delta_map[owner]

            token_delta = token_data["delta"] / (10 ** token_data["decimals"])
            sol_delta = sol_data["delta"] / (10 ** sol_data["decimals"])

            if token_delta == 0 or sol_delta == 0:
                print("⏩ Preskačeno: delta je 0")
                continue

            side = "BUY" if token_delta > 0 else "SELL"
            emoji = "🟢" if side == "BUY" else "🔴"
            price = abs(sol_delta / token_delta)
            value = abs(token_delta * price)

            print(f"📊 {side} - Token: {token_delta:.4f}, SOL: {sol_delta:.4f}, Vrednost: ${value:.2f}")

            if value < 500:
                print(f"⏬ Preskačem jer je vrednost samo ${value:.2f}")
                continue

            # UTC+2 vreme
            utc_time = datetime.utcfromtimestamp(block_time) + timedelta(hours=2)
            time_str = utc_time.strftime("%Y-%m-%d %H:%M:%S")

            message = (
                f"{emoji} <b>{side}</b>\n"
                f"<b>Adresa:</b> <a href='https://solscan.io/account/{owner}'>{owner}</a>\n"
                f"<b>Vrednost:</b> ${value:,.2f}\n"
                f"<b>Vreme:</b> {time_str} (UTC+2)"
            )
            send_telegram_message(message)

    return "OK", 200

if __name__ == "__main__":
    app.run(debug=True)














