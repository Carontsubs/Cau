import time
import yfinance as yf
import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv # 👈 Importem la funció per carregar .env

load_dotenv() 

TOKEN_TELEGRAM = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Parell i Llindar de preu
parell = "DOGE-USD"
PREU_ENTRADA = 0.243  
PREU_SORTIDA = 0.273

proper_avis = datetime.now()
c = 0

# Funció per enviar missatge a Telegram
def envia_missatge(text):
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": text}
    requests.get(url, params=params)

# Bucle de monitoratge
while True:

    try:
        ticker = yf.Ticker(parell)
        preu_actual = ticker.history(period="1d", interval="1m")["Close"][-1]
        
        # Llindars de preu
        if preu_actual >= PREU_ENTRADA and c < 4:
            envia_missatge(f"{parell} preu entrada {preu_actual:.3f}")
            c += 1             
        if preu_actual <= PREU_SORTIDA and c < 4:
            envia_missatge(f"{parell} preu sortida {preu_actual:.3f}")
            c += 1             

        # Avís cada cert temps
        if datetime.now() >= proper_avis:
            envia_missatge(f"{parell} està a {preu_actual:.3f}")
            proper_avis = datetime.now() + timedelta(hours=24)
            
    except Exception as e:
        # print("Error:", e)
        envia_missatge(f"Error:{e}")

    # espera en segons
    time.sleep(900)
