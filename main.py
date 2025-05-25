import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
MONITORED_TOKEN = "2AEU9yWk3dEGnVwRaKv4div5TarC4dn7axFLyz6zG4Pf"

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("❌ TELEGRAM_BOT_TOKEN ili TELEGRAM_CHAT_ID nisu postavljeni.")
else:
    print("✅ Telegram konfiguracija uspešno učitana.")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

def send_telegram_message(text):
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text
    }
    response = requests.post(TELEGRAM_API_URL, json=payload)
    print("Telegram response:", response.status_code, response.text)

@app.route("/", methods=["POST"])
def handle_webhook():
    data = request.get_json()
    print("\n\U0001F4E5 Primljen payload:", data)

    if not isinstance(data, list):
        return jsonify({"error": "Invalid payload"}), 400

    for tx in data:
        try:
            post_tokens = tx["meta"].get("postTokenBalances", [])
            pre_tokens = tx["meta"].get("preTokenBalances", [])

            for post, pre in zip(post_tokens, pre_tokens):
                if post["mint"] == MONITORED_TOKEN:
                    post_amt = int(post["uiTokenAmount"]["amount"])
                    pre_amt = int(pre["uiTokenAmount"]["amount"])
                    diff = abs(post_amt - pre_amt)
                    decimals = int(post["uiTokenAmount"]["decimals"])
                    ui_diff = diff / (10 ** decimals)

                    if ui_diff >= 100:
                        direction = "Kupovina" if post_amt > pre_amt else "Prodaja"
                        message = (
                            f"\U0001F4E2 Nova transakcija ({direction})\n\n"
                            f"Token: Introvert\n"
                            f"Količina: {ui_diff:.2f}\n"
                            f"Signature: {tx['transaction']['signatures'][0]}"
                        )
                        send_telegram_message(message)
        except Exception as e:
            print("Greška u obradi transakcije:", e)
            continue

    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)















