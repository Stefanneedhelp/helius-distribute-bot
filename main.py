import os import requests from flask import Flask, request

app = Flask(name)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") TOKEN_MINT = "2AEU9yWk3dEGnVwRaKv4div5TarC4dn7axFLyz6zG4Pf"  # nova adresa tokena

@app.route("/", methods=["POST"]) def webhook(): data = request.get_json() print("\n\U0001F4E5 Stigao payload:", data)

try:
    for tx in data:
        post_balances = tx["meta"].get("postTokenBalances", [])
        pre_balances = tx["meta"].get("preTokenBalances", [])

        for post, pre in zip(post_balances, pre_balances):
            if post["mint"] != TOKEN_MINT:
                continue

            amount_post = int(post["uiTokenAmount"]["amount"])
            amount_pre = int(pre["uiTokenAmount"]["amount"])
            diff = amount_post - amount_pre

            # ignorisi male transakcije
            decimals = int(post["uiTokenAmount"]["decimals"])
            amount_diff = diff / (10**decimals)
            if abs(amount_diff) < 100:
                continue

            direction = "Kupovina" if amount_diff > 0 else "Prodaja"

            signature = tx.get("transaction", {}).get("signatures", [""])[0]
            message = (
                f"\U0001F4E2 Nova transakcija!\n\n"
                f"Token: Introvert\n"
                f"Vrsta: {direction}\n"
                f"Iznos: {abs(amount_diff):,.2f}\n"
                f"Tx: {signature}"
            )

            send_telegram_message(message)
except Exception as e:
    print("Greska u obradi transakcije:", e)

return "ok"

def send_telegram_message(message): if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID: print("\u274C Telegram chat ID ili token nije postavljen!") return

url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
payload = {
    "chat_id": TELEGRAM_CHAT_ID,
    "text": message,
    "parse_mode": "HTML"
}
response = requests.post(url, json=payload)
print("\U0001F4E8 Telegram response:", response.status_code, response.text)

if name == "main": app.run(host="0.0.0.0", port=10000)


















