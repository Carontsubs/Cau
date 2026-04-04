import pdfplumber
import requests
import io
import re
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Carreguem les claus del fitxer .env
load_dotenv() 

# --- CONFIGURACIÓ TELEGRAM ---
TOKEN_BOT = os.getenv("TOKEN_TELEGRAM")
CHAT_ID = os.getenv("CHAT_ID")

def enviar_a_telegram(missatge):
    if not TOKEN_BOT or not CHAT_ID:
        print("Error: Falten les claus TOKEN_TELEGRAM o CHAT_ID al fitxer .env")
        return False
        
    url = f"https://api.telegram.org/bot{TOKEN_BOT}/sendMessage"
    # Usem Markdown per posar negretes
    data = {"chat_id": CHAT_ID, "text": missatge, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, data=data)
        return r.status_code == 200
    except Exception as e:
        print(f"Error enviant a Telegram: {e}")
        return False

def extreure_lectures_avui_generic(url):
    sigles = ["Gen", "Ex", "Lev", "Num", "Dt", "Jos", "Jue", "Rut", "1 Sam", "2 Sam", 
              "1 Re", "2 Re", "1 Cron", "2 Cron", "Esd", "Neh", "Tob", "Jdt", "Est", 
              "1 Mac", "2 Mac", "Job", "Sal", "Prov", "Ecl", "Eclo", "Sab", "Is", "Jer", 
              "Lam", "Bar", "Ez", "Dan", "Os", "Jl", "Am", "Abd", "Jon", "Miq", "Nah", 
              "Hab", "Sof", "Ag", "Zac", "Mal", "Mt", "Mc", "Lc", "Jn", "Hch", "Rom", 
              "1 Cor", "2 Cor", "Gal", "Ef", "Flp", "Col", "1 Tes", "2 Tes", "1 Tim", 
              "2 Tim", "Tit", "Flm", "Heb", "Sant", "1 Pe", "2 Pe", "1 Jn", "2 Jn", 
              "3 Jn", "Jds", "Ap"]
    
    mesos_es = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
    
    ara = datetime.now()
    dia_num = ara.day
    nom_mes = mesos_es[ara.month - 1]
    dia_seg = (ara + timedelta(days=1)).day

    try:
        response = requests.get(url, timeout=15)
        with pdfplumber.open(io.BytesIO(response.content)) as pdf:
            text_acumulat = ""
            pagina_inici = -1
            
            # 1. Trobar la pàgina on comença el dia
            for i in range(45, 250):
                p_text = pdf.pages[i].extract_text()
                if p_text and nom_mes in p_text.upper():
                    if re.search(rf"(?:^|\n){dia_num}\s", p_text):
                        pagina_inici = i
                        break
            
            if pagina_inici == -1: return None

            # 2. Llegim un bloc gran (10 pàgines)
            for j in range(pagina_inici, min(pagina_inici + 10, len(pdf.pages))):
                text_acumulat += pdf.pages[j].extract_text() + "\n"

            # 3. LÒGICA DE TALL GENÈRICA (La que t'ha funcionat bé)
            start_match = re.search(rf"(?:^|\n){dia_num}\s", text_acumulat)
            # Busquem el següent dia a partir d'un marge de seguretat
            end_match = re.search(rf"(?:^|\n){dia_seg}\s", text_acumulat[start_match.end() + 1000:])
            
            if start_match and end_match:
                bloc = text_acumulat[start_match.start() : start_match.end() + 1000 + end_match.start()]
            elif start_match:
                bloc = text_acumulat[start_match.start() : start_match.start() + 25000]
            else:
                bloc = text_acumulat

            # 4. Filtrar línies
            lectures = []
            for linia in bloc.split('\n'):
                l = linia.strip()
                es_biblica = any(l.startswith(f"{s} ") or l.startswith(f"- {s} ") for s in sigles)
                es_format = l.startswith("-") or re.search(r"^\d\.\ª", l) or l.startswith("Secuencia")
                
                if (es_biblica or es_format) and "CALENDARIO" not in l.upper() and len(l) > 8:
                    # Netegem espais fora de la f-string per evitar l'error de la barra invertida
                    text_net = re.sub(r'\s+', ' ', l)
                    lectures.append(f"• {text_net}")

            return "\n".join(lectures)

    except Exception as e:
        print(f"Error PDF: {e}")
        return None

# --- EXECUCIÓ ---
url_pdf = "https://www.conferenciaepiscopal.es/wp-content/uploads/2026/01/Calendario-Liturgico-CEE-2026.pdf"
lectures_text = extreure_lectures_avui_generic(url_pdf)

if lectures_text:
    data_str = datetime.now().strftime('%d/%m/%Y')
    missatge = f"*LECTURES D'AVUI ({data_str})*\n\n{lectures_text}"
    if enviar_a_telegram(missatge):
        print("Lectures enviades correctament a Telegram!")
    else:
        print("Error enviant el missatge.")
else:
    print("No s'han pogut extreure les lectures.")