import pdfplumber
import requests
import io
import re
from datetime import datetime, timedelta

def extreure_lectures_completes_generic(url, data_obj):
    # Llista oficial de sigles per identificar cada lectura
    sigles = ["Gen", "Ex", "Lev", "Num", "Dt", "Jos", "Jue", "Rut", "1 Sam", "2 Sam", 
              "1 Re", "2 Re", "1 Cron", "2 Cron", "Esd", "Neh", "Tob", "Jdt", "Est", 
              "1 Mac", "2 Mac", "Job", "Sal", "Prov", "Ecl", "Eclo", "Sab", "Is", "Jer", 
              "Lam", "Bar", "Ez", "Dan", "Os", "Jl", "Am", "Abd", "Jon", "Miq", "Nah", 
              "Hab", "Sof", "Ag", "Zac", "Mal", "Mt", "Mc", "Lc", "Jn", "Hch", "Rom", 
              "1 Cor", "2 Cor", "Gal", "Ef", "Flp", "Col", "1 Tes", "2 Tes", "1 Tim", 
              "2 Tim", "Tit", "Flm", "Heb", "Sant", "1 Pe", "2 Pe", "1 Jn", "2 Jn", 
              "3 Jn", "Jds", "Ap"]
    
    mesos_es = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
    
    dia_actual = data_obj.day
    nom_mes = mesos_es[data_obj.month - 1]
    
    data_seguent = data_obj + timedelta(days=1)
    dia_seguent = data_seguent.day

    try:
        response = requests.get(url, timeout=15)
        with pdfplumber.open(io.BytesIO(response.content)) as pdf:
            text_ampli = ""
            pagina_inici = -1
            
            # 1. Localitzem la pàgina on comença el dia (o el mes si el dia és "rebel")
            for i in range(45, 250):
                p_text = pdf.pages[i].extract_text()
                if p_text and nom_mes in p_text.upper():
                    # Busquem el número del dia com a inici de línia
                    if re.search(rf"(?:^|\n){dia_actual}\s", p_text):
                        pagina_inici = i
                        break
            
            # Si no trobem el número del dia (cas de títols grans), busquem per proximitat al mes
            if pagina_inici == -1:
                for i in range(45, 250):
                    p_text = pdf.pages[i].extract_text()
                    if p_text and nom_mes in p_text.upper():
                        pagina_inici = i
                        break

            # 2. Llegim un bloc gran (10 pàgines) per no deixar-nos res de la Vigília
            for j in range(pagina_inici, min(pagina_inici + 10, len(pdf.pages))):
                text_ampli += pdf.pages[j].extract_text() + "\n"

            # 3. Delimitem el bloc del dia exactament
            # Busquem on comença el dia actual i on comença el següent
            regex_dia = rf"(?:^|\n){dia_actual}\s"
            regex_seg = rf"(?:^|\n){dia_seguent}\s"
            
            match_inici = re.search(regex_dia, text_ampli)
            match_final = re.search(regex_seg, text_ampli[match_inici.end() if match_inici else 0:])
            
            if match_inici and match_final:
                bloc_final = text_ampli[match_inici.start() : match_inici.end() + match_final.start()]
            elif match_inici:
                bloc_final = text_ampli[match_inici.start() : match_inici.start() + 25000] # Bloc molt gran per seguretat
            else:
                bloc_final = text_ampli

            # 4. Extracció neta usant les SIGLES bíbliques
            lectures = []
            for linia in bloc_final.split('\n'):
                l = linia.strip()
                # Una línia és lectura si comença per sigla, guió o format "1.ª"
                es_biblica = any(l.startswith(f"{s} ") or l.startswith(f"- {s} ") for s in sigles)
                es_format = l.startswith("-") or re.search(r"^\d\.\ª", l) or l.startswith("Secuencia")
                
                if (es_biblica or es_format):
                    if "CALENDARIO" not in l.upper() and len(l) > 8:
                        # Netegem espais dobles i caràcters estranys de salt de pàgina
                        lectures.append(re.sub(r'\s+', ' ', l))

            return "\n".join(lectures)

    except Exception as e:
        return f"Error en l'extracció genèrica: {e}"

# --- EXECUCIÓ ---
url_pdf = "https://www.conferenciaepiscopal.es/wp-content/uploads/2026/01/Calendario-Liturgico-CEE-2026.pdf"
avui = datetime.now().date()
dema = avui + timedelta(days=1)

print(f"--- LECTURES COMPLETES D'AVUI ({avui.day}/{avui.month}/2026) ---")
print(extreure_lectures_completes_generic(url_pdf, avui))

print(f"\n--- LECTURES COMPLETES DE DEMÀ ({dema.day}/{dema.month}/2026) ---")
print(extreure_lectures_completes_generic(url_pdf, dema))