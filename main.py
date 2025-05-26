import os
import requests
from flask import Flask, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
DEXSCREENER_API = "https://api.dexscreener.com/latest/dex/tokens/"
MONITORED_MINT = os.getenv("MONITORED_MINT")  # opcionalno, možeš i izostaviti

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Telegram greška: {e}")

def get_token_price(token_address):
    try:
        url = f"{DEXSCREENER_API}{token_address}"
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
        price = float(data['pairs'][0]['priceUsd'])
        return price
    except Exception as e:
        print("Greška kod preuzimanja cene:", e)
        return None

@app.route("/", methods=["POST"])
def handle_webhook():
    data = request.get_json()
    print("📥 Stigao payload:", data)

    try:
        tx = data[0]
        log_messages = tx.get("meta", {}).get("logMessages", [])
        token_balances = tx.get("meta", {}).get("postTokenBalances", [])

        # ✅ FILTER: dozvoli samo transakcije koje imaju "Swap" ili "Transfer" u logovima
        if not any("Swap" in log or "Transfer" in log for log in log_messages):
            print("⛔ Preskačem jer nije swap/trade transakcija.")
            return "", 200

        mint_addresses = [tb["mint"] for tb in token_balances]
        print("Mint adrese u transakciji:", mint_addresses)

        # koristi prvi match za prikaz
        for tb in token_balances:
            mint = tb["mint"]
            amount = float(tb["uiTokenAmount"]["uiAmount"])
            if amount == 0:
                continue

            price = get_token_price(mint)
            if price is None:
                print("❌ Nema cene sa DEX Screener-a.")
                return "", 200

            total_value = amount * price
            if total_value < 100:
                print(f"Preskačem transakciju ispod $100: {total_value}")
                return "", 200

            message = f"💸 Token: <code>{mint}</code>\n📊 Količina: {amount:.6f}\n💰 Vrednost: ${total_value:.2f}"
            send_telegram_message(message)
            return "", 200

    except Exception as e:
        print("❌ Greška u obradi transakcije:", e)
        return "", 500

    return "", 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)


















