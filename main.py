import os
import json
import requests
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
DEXSCREENER_API = "https://api.dexscreener.com/latest/dex/tokens/"
MONITORED_MINT = os.getenv("MONITORED_MINT")

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


def send_telegram_message(text):
    data = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    response = requests.post(TELEGRAM_URL, json=data)
    print("[TELEGRAM]", response.status_code, response.text)


def fetch_token_price(mint):
    try:
        response = requests.get(DEXSCREENER_API + mint)
        data = response.json()
        return float(data["pairs"][0]["priceUsd"])
    except:
        return 0.0


@app.route("/", methods=["POST"])
def handle_webhook():
    payload = request.json
    print("\U0001F4E5 Stigao payload:", json.dumps(payload, indent=2))

    for tx_data in payload:
        if "meta" not in tx_data or "postTokenBalances" not in tx_data["meta"]:
            continue

        pre_token_balances = tx_data["meta"].get("preTokenBalances", [])
        post_token_balances = tx_data["meta"].get("postTokenBalances", [])
        pre_token_balances_by_index = {
            b["accountIndex"]: b for b in pre_token_balances
        }

        for token in post_token_balances:
            if token.get("mint") != MONITORED_MINT:
                continue

            account_index = token["accountIndex"]
            new_amount = float(token["uiTokenAmount"]["uiAmount"])
            old_amount = float(pre_token_balances_by_index.get(account_index, {"uiTokenAmount": {"uiAmount": 0}})["uiTokenAmount"]["uiAmount"])
            amount_diff = new_amount - old_amount

            if amount_diff == 0:
                continue

            tx_type = "BUY ✅" if amount_diff > 0 else "SELL \U0001F53B"
            readable_time = datetime.utcfromtimestamp(tx_data["blockTime"]).strftime('%Y-%m-%d %H:%M:%S UTC')

            price = fetch_token_price(MONITORED_MINT)
            usd_value = abs(amount_diff * price)

            if usd_value < 100:
                print(f"Preskačem token ispod $100: {usd_value:.4f}")
                continue

            message = f"""
📈 <b>{tx_type}</b> of <b>{abs(amount_diff):,.4f} tokens</b>
💸 Value: <b>${usd_value:,.2f}</b>
🕒 Time: <code>{readable_time}</code>
🔗 <a href='https://dexscreener.com/solana/{MONITORED_MINT}'>DEX View</a>
"""
            send_telegram_message(message.strip())

    return "ok"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)



















