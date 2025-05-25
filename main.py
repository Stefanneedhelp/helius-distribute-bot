
import os
import requests
from flask 
import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TOKEN_SYMBOL = "Introvert"


@app.route("/", methods=["POST"])
def webhook():
    data = request.json
    print("\U0001F4E5 Stigao payload:", data)

    try:
        for tx in data:
            signature = tx.get("transaction", {}).get("signatures", [""])[0]
            pre_balances = tx.get("meta", {}).get("preTokenBalances", [])
            post_balances = tx.get("meta", {}).get("postTokenBalances", [])

            if not pre_balances or not post_balances:
                continue

            for pre, post in zip(pre_balances, post_balances):
                pre_amt = int(pre['uiTokenAmount']['amount']) / (10 ** pre['uiTokenAmount']['decimals'])
                post_amt = int(post['uiTokenAmount']['amount']) / (10 ** post['uiTokenAmount']['decimals'])
                
                delta = post_amt - pre_amt
                
                if abs(delta) < 100:
                    continue  # preskoci ako nije preko 100$ (u token jedinicama)

                tx_type = "Kupovina" if delta > 0 else "Prodaja"
                
                msg = (
                    f"\U0001F4E2 Nova transakcija!
"
                    f"Vrsta: {tx_type}\n"
                    f"Token: {TOKEN_SYMBOL}\n"
                    f"Količina: {abs(round(delta, 3))}\n"
                    f"Signature: {signature}"
                )
                
                send_telegram(msg)

    except Exception as e:
        print("\u274C Greska u obradi payloada:", str(e))

    return jsonify({"status": "ok"})


def send_telegram(message):
    if not TELEGRAM_CHAT_ID:
        print("\u274C CHAT_ID nije postavljen!")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    response = requests.post(url, json=payload)
    print("\U0001F4E8 Telegram response:", response.status_code, response.text)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)















