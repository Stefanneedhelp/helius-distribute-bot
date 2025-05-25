
from flask import Flask, request import os import requests from dotenv import load_dotenv

load_dotenv()

app = Flask(name)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") MINT_ADDRESS = os.getenv("MINT_ADDRESS")  # nova adresa tokena koji se prati

@app.route('/', methods=['POST']) def webhook(): data = request.get_json() print("\n\U0001F4E5 Stigao payload:", data)

if not data:
    return '', 200

try:
    for tx in data:
        # Proveri da li je u pitanju token koji pratimo
        token_balances = tx.get("meta", {}).get("postTokenBalances", [])
        if any(tb.get("mint") == MINT_ADDRESS for tb in token_balances):

            # Proveri tip transakcije (prodaja/kupovina)
            logovi = tx.get("meta", {}).get("logMessages", [])
            tip = ""
            for log in logovi:
                if "Instruction: Sell" in log:
                    tip = "Prodaja"
                    break
                elif "Instruction: Buy" in log:
                    tip = "Kupovina"
                    break

            # Cene se nalaze kod programa JUP i pAMM, ali ovde pojednostavljeno
            signature = tx.get("transaction", {}).get("signatures", [""])[0]
            poruka = f"\U0001F4E2 Nova transakcija!\n\nTip: {tip or 'Nepoznat'}\nSignature: {signature}"

            # Pošalji na Telegram
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID, "text": poruka}
            )

except Exception as e:
    print("\n\u26A0\uFE0F Greska pri obradi:", e)

return '', 200
















