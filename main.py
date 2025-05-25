import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TOKEN_MINT = "4fJVpHzgaQ5F5BmFWpLrVf7zdmkYJccgcz6XMQo1pump"

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


def send_telegram_message(message):
    if not CHAT_ID:
        print("CHAT_ID nije postavljen!")
        return

    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    response = requests.post(TELEGRAM_URL, json=payload)
    print("\U0001F4E8 Telegram response:", response.status_code, response.text)


@app.route('/', methods=['POST'])
def handle_helius_webhook():
    data = request.json
    print("\U0001F4E5 Stigao payload:", data)

    for tx in data:
        try:
            pre_tokens = tx['meta']['preTokenBalances']
            post_tokens = tx['meta']['postTokenBalances']
            signature = tx['transaction']['signatures'][0]

            for pre, post in zip(pre_tokens, post_tokens):
                if pre['mint'] != TOKEN_MINT:
                    continue

                amount_pre = int(pre['uiTokenAmount']['amount']) / (10 ** pre['uiTokenAmount']['decimals'])
                amount_post = int(post['uiTokenAmount']['amount']) / (10 ** post['uiTokenAmount']['decimals'])

                delta = amount_post - amount_pre
                usd_price = abs(delta) * 0.0065  # hardcoded cena tokena u USD

                if usd_price < 100:
                    continue

                action = "Kupovina" if delta > 0 else "Prodaja"

                message = (
                    f"📢 Nova transakcija!
"
                    f"Tip: {action}\n"
                    f"Iznos (u USD): ${usd_price:.2f}\n"
                    f"Signature: {signature}"
                )
                send_telegram_message(message)
                break

        except Exception as e:
            print("Greska u obradi transakcije:", e)

    return jsonify({"status": "ok"})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)









