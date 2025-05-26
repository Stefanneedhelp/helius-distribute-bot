import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
DEXSCREENER_API = "https://api.dexscreener.com/latest/dex/tokens/"
MONITORED_MINT = os.getenv("MONITORED_MINT")

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print("Greška pri slanju poruke:", e)

def get_token_price(mint_address):
    url = DEXSCREENER_API + mint_address
    try:
        response = requests.get(url)
        data = response.json()
        if data.get("pairs"):
            price = data["pairs"][0]["priceUsd"]
            return float(price)
    except Exception as e:
        print("Greška pri dobijanju cene:", e)
    return None

@app.route("/", methods=["POST"])
def webhook():
    payload = request.json
    print("📥 Stigao payload:", payload)

    if not MONITORED_MINT:
        print("❌ Nema definisane mint adrese.")
        return jsonify({"error": "No mint address set"}), 400

    found = False
    for tx in payload:
        balances = tx.get("meta", {}).get("postTokenBalances", [])
        for balance in balances:
            mint = balance.get("mint")
            if mint == MONITORED_MINT:
                found = True
                amount_raw = int(balance.get("uiTokenAmount", {}).get("amount", "0"))
                decimals = int(balance.get("uiTokenAmount", {}).get("decimals", 0))
                amount = amount_raw / (10 ** decimals)

                usd_price = get_token_price(mint)
                if usd_price is None:
                    continue

                total_value = amount * usd_price
                print(f"🔍 Transakcija za {amount:.4f} tokena × ${usd_price:.6f} = ${total_value:.2f}")

                if total_value >= 100:
                    message = (
                        f"💸 Transakcija iznad $100:\n"
                        f"<b>{mint}</b>\n\n"
                        f"📦 Iznos: <b>{amount:.4f}</b>\n"
                        f"💰 Cena: <b>${usd_price:.6f}</b>\n"
                        f"📊 Ukupno: <b>${total_value:.2f}</b>"
                    )
                    send_telegram_message(message)
                else:
                    print(f"Preskačem token ispod $100: {total_value:.2f}")
                break

    if not found:
        print("⚠️ Nema relevantnih transakcija za mint:", MONITORED_MINT)

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)

















