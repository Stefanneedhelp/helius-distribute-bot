from flask import Flask, request
import requests
import os

app = Flask(__name__)

# Preuzmi podatke iz Render okruženja ili koristi fallback
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    print(f"📨 Telegram response: {response.status_code} {response.text}")

@app.route("/", methods=["POST"])
def handle_webhook():
    try:
        data = request.get_json()
        print("📥 Stigao payload:", data)

        transactions = data if isinstance(data, list) else [data]

        for tx in transactions:
            try:
                pre = tx.get("meta", {}).get("preTokenBalances", [])
                post = tx.get("meta", {}).get("postTokenBalances", [])
                sig = tx["transaction"]["signatures"][0]

                for pre_bal, post_bal in zip(pre, post):
                    mint = pre_bal["mint"]
                    owner = pre_bal["owner"]

                    if mint != post_bal["mint"] or owner != post_bal["owner"]:
                        continue  # sigurnosna provera

                    pre_amount = float(pre_bal["uiTokenAmount"]["uiAmount"])
                    post_amount = float(post_bal["uiTokenAmount"]["uiAmount"])
                    delta = round(post_amount - pre_amount, 6)

                    if abs(delta) >= 100:
                        action = "🟢 Kupovina" if delta > 0 else "🔴 Prodaja"

                        send_telegram_message(
                            f"{action} detektovana!\n\n"
                            f"💸 Token: `{mint}`\n"
                            f"📊 Promena: *{abs(delta):,.2f}*\n"
                            f"🔗 Signature: `{sig}`"
                        )

            except Exception as e:
                print(f"❌ Greška u analizi transakcije: {e}")

        return "OK", 200
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return "Error", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)







