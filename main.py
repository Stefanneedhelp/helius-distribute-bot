
import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
MONITORED_MINT = os.getenv("MONITORED_MINT")

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


def send_telegram_message(message):
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    response = requests.post(API_URL, json=payload)
    print("📨 Telegram response:", response.status_code, response.text)


@app.route('/', methods=['POST'])
def handle_webhook():
    data = request.get_json()
    print("📥 Stigao payload:", data)

    for tx in data:
        try:
            mint_addresses = [b['mint'] for b in tx['meta']['postTokenBalances']]
            if MONITORED_MINT not in mint_addresses:
                continue

            tx_type = 'Kupovina' if 'Buy' in str(tx['meta'].get('logMessages', [])) else 'Prodaja'
            signature = tx['transaction']['signatures'][0]

            # Traži odgovarajući zapis sa mint adresom
            token_info = next((b for b in tx['meta']['postTokenBalances'] if b['mint'] == MONITORED_MINT), None)

            if not token_info:
                continue

            ui_amount = token_info['uiTokenAmount'].get('uiAmount', 0)

            sol_price = get_sol_price()
            token_price_in_sol = estimate_token_price(tx)
            total_usd = round(ui_amount * sol_price * token_price_in_sol, 2)

            if total_usd < 100:
                continue

            message = (
                f"\U0001F4E2 Nova transakcija!\n\n"
                f"Tip: {tx_type}\n"
                f"Iznos: {total_usd} USD\n"
                f"Signature: {signature}"
            )
            send_telegram_message(message)

        except Exception as e:
            print("Greška pri obradi transakcije:", e)

    return jsonify({"status": "ok"})


def get_sol_price():
    try:
        res = requests.get("https://price.jup.ag/v4/price?ids=SOL")
        return res.json()['data']['SOL']['price']
    except:
        return 0


def estimate_token_price(tx):
    try:
        post = tx['meta']['postTokenBalances']
        sol_amount = 0
        token_amount = 0

        for b in post:
            if b['mint'] == MONITORED_MINT:
                token_amount = b['uiTokenAmount']['uiAmount']
            if b['mint'] == "So11111111111111111111111111111111111111112":
                sol_amount = b['uiTokenAmount']['uiAmount']

        return sol_amount / token_amount if token_amount else 0
    except:
        return 0


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

















