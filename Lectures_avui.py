import pdfplumber
import requests
import io
import re
from datetime import datetime, timedelta

def extreure_lectures_generic_pur(url):
    # Sigles bíbliques oficials (la teva llista)
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
            
            # 1. Trobar la pàgina on comença el mes i el dia d'avui
            for i in range(45, 250):
                p_text = pdf.pages[i].extract_text()
                if p_text and nom_mes in p_text.upper():
                    if re.search(rf"(?:^|\n){dia_num}\s", p_text):
                        pagina_inici = i
                        break
            
            if pagina_inici == -1: return f"No s'ha trobat el dia {dia_num}."

            # 2. Llegim un bloc gran de pàgines (per si el dia és molt llarg)
            for j in range(pagina_inici, min(pagina_inici + 10, len(pdf.pages))):
                text_acumulat += pdf.pages[j].extract_text() + "\n"

            # 3. LÒGICA GENÈRICA DE TALL:
            # Busquem la línia que comença per "4 " i la que comença per "5 "
            # El regex '^4\s' o '\n4\s' assegura que és el número del dia i no un versicle
            start_match = re.search(rf"(?:^|\n){dia_num}\s", text_acumulat)
            # Busquem el següent dia (el 5) que estigui a partir de 1000 caràcters de l'inici
            # per evitar confusions amb números de pàgina o versicles inicials.
            end_match = re.search(rf"(?:^|\n){dia_seg}\s", text_acumulat[start_match.end() + 1000:])
            
            if start_match and end_match:
                bloc = text_acumulat[start_match.start() : start_match.end() + 1000 + end_match.start()]
            else:
                bloc = text_acumulat[start_match.start() : start_match.start() + 20000]

            # 4. Filtrar línies de lectura usant les sigles
            lectures = []
            for linia in bloc.split('\n'):
                l = linia.strip()
                
                # Una línia és lectura si comença per una sigla de la llista
                # o per formats estàndard (- , 1.ª, Secuencia)
                es_biblica = any(l.startswith(f"{s} ") or l.startswith(f"- {s} ") for s in sigles)
                es_format = l.startswith("-") or re.search(r"^\d\.\ª", l) or l.startswith("Secuencia")
                
                if (es_biblica or es_format):
                    if "CALENDARIO" not in l.upper() and len(l) > 8:
                        lectures.append(re.sub(r'\s+', ' ', l))

            return "\n".join(lectures)

    except Exception as e:
        return f"Error: {e}"

# --- EXECUCIÓ ---
url_pdf = "https://www.conferenciaepiscopal.es/wp-content/uploads/2026/01/Calendario-Liturgico-CEE-2026.pdf"
print(f"--- LECTURES D'AVUI ({datetime.now().strftime('%d/%m/%Y')}) ---")
print(extreure_lectures_generic_pur(url_pdf))