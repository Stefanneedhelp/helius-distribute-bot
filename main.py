import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TOKEN_MINT = "4fJVpHzgaQ5F5BmFWpLrVf7zdmkYJccgcz6XMQo1pump"  # Introvert token mint

@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()
    print("📥 Stigao payload:", data)

    try:
        transactions = data if isinstance(data, list) else [data]
        for tx in transactions:
            meta = tx.get("meta")
            if not meta or meta.get("err") is not None:
                continue

            signature = tx.get("transaction", {}).get("signatures", [""])[0]
            post_balances = meta.get("postTokenBalances", [])
            pre_balances = meta.get("preTokenBalances", [])

            for post, pre in zip(post_balances, pre_balances):
                try:
                    if post["mint"] == TOKEN_MINT and pre["mint"] == TOKEN_MINT:
                        amount_post = int(post["uiTokenAmount"]["amount"])
                        amount_pre = int(pre["uiTokenAmount"]["amount"])
                        decimals = int(post["uiTokenAmount"]["decimals"])
                        diff = (amount_post - amount_pre) / (10 ** decimals)

                        usd_price = 0.0000042  # Približna cena Introvert tokena
                        usd_amount = abs(diff) * usd_price

                        if usd_amount < 100:
                            continue  # Preskoči transakcije manje od 100 USD

                        if diff > 0:
                            tip_transakcije = "KUPovina"
                        else:
                            tip_transakcije = "PRODaja"

                        message = (
                            f"📢 Nova transakcija!\n\n"
                            f"Tip: {tip_transakcije}\n"
                            f"Iznos: {usd_amount:.2f} USD\n"
                            f"Signature: {signature}"
                        )

                        send_telegram_message(message)
                except Exception as e:
                    print(f"❌ Greska u obradi balansa: {e}")
                    continue

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return jsonify({"error": str(e)}), 500


def send_telegram_message(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ TELEGRAM_BOT_TOKEN ili CHAT_ID nije postavljen.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    response = requests.post(url, json=payload)
    print(f"📨 Telegram response: {response.status_code} {response.text}")


if __name__ == "__main__":
    app.run(debug=True)









