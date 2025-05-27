import os
from flask import Flask, request
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
MONITORED_MINT = os.getenv("MONITORED_MINT")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

def send_telegram_message(message):
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        r = requests.post(TELEGRAM_API, json=payload)
        print(f"✅ Poruka poslata: {r.status_code}")
    except Exception as e:
        print(f"❌ Greska u slanju poruke: {e}")

@app.route("/", methods=["POST"])
def webhook():
    payload = request.json
    print("✅ Webhook primljen.")

    for tx in payload:
        logs = tx.get("meta", {}).get("logMessages", [])
        if not any("Instruction: Swap" in log for log in logs):
            continue

        pre_balances = tx.get("meta", {}).get("preTokenBalances", [])
        post_balances = tx.get("meta", {}).get("postTokenBalances", [])
        block_time = tx.get("blockTime")
        timestamp = datetime.utcfromtimestamp(block_time).strftime("%Y-%m-%d %H:%M:%S UTC")

        mint_deltas = {}

        for pre in pre_balances:
            mint = pre.get("mint")
            owner = pre.get("owner")
            amount = int(pre["uiTokenAmount"]["amount"])
            decimals = int(pre["uiTokenAmount"]["decimals"])
            mint_deltas[(mint, owner)] = {"pre": amount, "decimals": decimals}

        for post in post_balances:
            mint = post.get("mint")
            owner = post.get("owner")
            amount = int(post["uiTokenAmount"]["amount"])
            key = (mint, owner)
            if key in mint_deltas:
                pre = mint_deltas[key]["pre"]
                decimals = mint_deltas[key]["decimals"]
                delta = amount - pre
                mint_deltas[key].update({"post": amount, "delta": delta})

        for (mint, owner), data in mint_deltas.items():
            if mint == MONITORED_MINT and "delta" in data:
                delta_token = data["delta"] / (10 ** data["decimals"])
            elif mint == "So11111111111111111111111111111111111111112" and "delta" in data:
                delta_sol = data["delta"] / (10 ** data["decimals"])
                sol_owner = owner

        if 'delta_token' in locals() and 'delta_sol' in locals() and delta_token != 0:
            price = abs(delta_sol / delta_token)
            value = abs(delta_token * price)
            side = "BUY" if delta_token > 0 else "SELL"

            if value >= 100:
                message = (
                    f"🔁 <b>SWAP transakcija preko $100</b>\n\n"
                    f"<b>{side} ${value:,.2f}</b>\n"
                    f"<b>Token:</b> {MONITORED_MINT}\n"
                    f"<b>Promena:</b> {abs(delta_token):,.4f}\n"
                    f"<b>Cena:</b> ${price:.4f}\n"
                    f"<b>Korisnik:</b> {sol_owner}\n"
                    f"<b>Vreme:</b> {timestamp}"
                )
                send_telegram_message(message)

    return "OK", 200

if __name__ == "__main__":
    app.run(debug=True)

















