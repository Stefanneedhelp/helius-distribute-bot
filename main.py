import os
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()
    try:
        # Provera da li je transakcija validna
        transaction = data[0]  # <- zato što Helius šalje listu
        signature = transaction.get("transaction", {}).get("signatures", [""])[0]
        amount = transaction.get("meta", {}).get("postBalances", [])[0]  # primer

        message = f"📢 Nova transakcija!\n\nSignature: {signature}\nAmount: {amount}"
        requests.post(TELEGRAM_API_URL, json={"chat_id": CHAT_ID, "text": message})
        return "OK", 200
    except Exception as e:
        print("Webhook error:", str(e))
        return "Error", 500

@app.route("/", methods=["GET"])
def home():
    return "Webhook radi 🚀", 200





