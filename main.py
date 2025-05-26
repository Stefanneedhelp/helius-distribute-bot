
import os 
import requests 
from flask import Flask, request

app = Flask(name)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID") MONITORED_TOKEN = "2AEU9yWk3dEGnVwRaKv4div5TarC4dn7axFLyz6zG4Pf"

Jupiter program ID

JUPITER_PROGRAM_ID = "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4"

@app.route("/", methods=["POST"]) def handle_webhook(): data = request.json if not data: return "No data", 400

for tx in data:
    try:
        logs = tx.get("meta", {}).get("logMessages", [])
        instructions = tx.get("meta", {}).get("innerInstructions", [])
        post_balances = tx.get("meta", {}).get("postTokenBalances", [])
        pre_balances = tx.get("meta", {}).get("preTokenBalances", [])
        program_ids = [ix.get("programIdIndex") for i in instructions for ix in i.get("instructions", [])]

        # Provera da li je Jupiter swap
        if not any(JUPITER_PROGRAM_ID in l for l in logs):
            continue

        # Pronadji vrednosti tokena pre i posle
        pre_amount = next((float(p["uiTokenAmount"]["uiAmount"]) for p in pre_balances if p["mint"] == MONITORED_TOKEN), 0)
        post_amount = next((float(p["uiTokenAmount"]["uiAmount"]) for p in post_balances if p["mint"] == MONITORED_TOKEN), 0)
        delta = round(post_amount - pre_amount, 6)

        # Provera da li je delta veci od 100$ (pretpostavka 1 token = 1 USD ako nemamo oracle)
        if abs(delta) < 100:
            continue

        direction = "Kupovina" if delta > 0 else "Prodaja"

        message = (
            f"\ud83d\



















