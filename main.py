import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
INTROVERT_MINT = "4fJVpHzgaQ5F5BmFWpLrVf7zdmkYJccgcz6XMQo1pump"
INTROVERT_PRICE = 0.0065  # Ažuriraj ako se cena menja

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    response = requests.post(url, data=data)
    print("📨 Telegram response:", response.status_code, response.text)

@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()
    print("📥 Stigao payload:", data)

    try:
        for tx in data:
            meta = tx.get("meta", {})
            if meta.get("err") is not None:
                continue  # preskoči failovane tx

            post_tokens = meta.get("postTokenBalances", [])
            pre_tokens = meta.get("preTokenBalances", [])
            signature = tx.get("transaction", {}).get("signatures", [""])[0]

            # Tražimo Introvert token
            for i, post in enumerate(post_tokens):
                if post["mint"] != INTROVERT_MINT:
                    continue

                post_amt = float(post["uiTokenAmount"]["amount"])
                pre_amt = float(pre_tokens[i]["uiTokenAmount"]["amount"])

                delta = post_amt - pre_amt
                usd_total = abs(delta) * INTROVERT_PRICE

                if usd_total < 100:
                    continue  # ignoriši male tx

                if delta > 0:
                    tip = "Kupovina"
                elif delta < 0:
                    tip = "Prodaja"
                else:
                    continue  # nema promene

                message = (
                    f"📢 Nova transakcija detektovana!\n\n"
                    f"Tip: {tip}\n"
                    f"Iznos: {abs(delta):,.2f} INTROVERT\n"
                    f"Vrednost: ${usd_total:,.2f}\n"
                    f"Signature: {signature}"
                )
                send_telegram_message(message)

    except Exception as e:
        print("❌ Greška:", str(e))
        return jsonify({"error": str(e)}), 500

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(debug=True)








