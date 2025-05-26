import os
import requests
import telegram
from flask import Flask, request, jsonify

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
MONITORED_MINT = "2AEU9yWk3dEGnVwRaKv4div5TarC4dn7axFLyz6zG4Pf"
DEXSCREENER_API = "https://api.dexscreener.com/latest/dex/tokens/"

tg_bot = telegram.Bot(token=BOT_TOKEN)

@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()
    print("\U0001F4E5 Stigao payload:", data)

    if not data:
        return "No data", 400

    for tx in data:
        try:
            transaction = tx.get("transaction", {})
            meta = tx.get("meta", {})
            pre_token_balances = meta.get("preTokenBalances", [])
            post_token_balances = meta.get("postTokenBalances", [])
            block_time = tx.get("blockTime")
            log_messages = meta.get("logMessages", [])

            if not any("swap" in log.lower() for log in log_messages):
                continue

            for pre, post in zip(pre_token_balances, post_token_balances):
                mint = post.get("mint")
                if mint != MONITORED_MINT:
                    continue

                pre_balance = float(pre.get("uiTokenAmount", {}).get("uiAmount", 0))
                post_balance = float(post.get("uiTokenAmount", {}).get("uiAmount", 0))
                delta = post_balance - pre_balance

                if delta == 0:
                    continue

                try:
                    price_response = requests.get(DEXSCREENER_API + MONITORED_MINT)
                    price_data = price_response.json()
                    price = float(price_data['pairs'][0]['priceUsd'])
                except Exception as e:
                    print("Greška pri dohvaćanju cene:", e)
                    continue

                usd_value = abs(delta * price)

                if usd_value < 100:
                    print(f"Preskačem token ispod $100: {usd_value:.4f}")
                    continue

                action = "BUY" if delta > 0 else "SELL"
                timestamp = block_time

                message = f"\u2728 {action} ${usd_value:.2f}\nMint: {mint}\nTime: {timestamp}"
                tg_bot.send_message(chat_id=CHAT_ID, text=message)

        except Exception as e:
            print("Greška u obradi transakcije:", e)

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))




















