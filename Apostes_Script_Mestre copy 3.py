import requests
from bs4 import BeautifulSoup
import csv
import os
from collections import Counter
from itertools import combinations
from datetime import datetime, timedelta
from dotenv import load_dotenv # Importem la funció per carregar .env

# Carrega les variables d'entorn del fitxer .env
load_dotenv() 

# Obtenim la clau d'API. Si no la troba, generarà un error.
TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM")
CHAT_ID =  os.getenv("TELEGRAM_CHAT_ID")

FITXER_PRIMI = "Lotoideas.com - Histórico de Resultados - Primitiva - 2013 a 202X(1).csv"
FITXER_BONO = "Lotoideas.com - Histórico de Resultados - Bonoloto - 2013 a 202X(1).csv"
FITXER_NETA = "estadistiques_loteries_NETA.csv"
HEADERS = {'User-Agent': 'Mozilla/5.0'}

def enviar_telegram(missatge):
    """Envia el tiquet de jugada directament al teu Telegram"""
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": missatge, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, data=data)
        if r.status_code == 200:
            print("📲 Notificació enviada a Telegram correctament.")
        else:
            print(f"⚠️ Error enviant a Telegram: {r.text}")
    except Exception as e:
        print(f"❌ Error de connexió amb Telegram: {e}")

def parsejar_data_flexible(data_str):
    data_netejada = data_str.split(' ')[0].replace('-', '/')
    for fmt in ["%d/%m/%Y", "%Y/%m/%d"]:
        try: return datetime.strptime(data_netejada, fmt)
        except: continue
    return None

def actualitzar_dades():
    print("🛰️  FASE 1: ACTUALITZANT DADES DES DE LA WEB...")
    tasques = [
        ("https://www.lotoideas.com/primitiva-resultados-historicos-de-todos-los-sorteos/", FITXER_PRIMI, "gid=1"),
        ("https://www.lotoideas.com/bonoloto-resultados-historicos-de-todos-los-sorteos/", FITXER_BONO, "gid=0")
    ]
    for url, nom, gid in tasques:
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            link = next((a['href'] for a in soup.find_all('a', href=True) if "output=csv" in a['href'] and gid in a['href']), None)
            if link:
                with open(nom, 'wb') as f: f.write(requests.get(link).content)
                print(f"✅ {nom} descarregat.")
        except: print(f"❌ Error descarregant {nom}.")

    dades = []
    for f_nom, tipus in [(FITXER_PRIMI, "Primitiva"), (FITXER_BONO, "Bonoloto")]:
        if os.path.exists(f_nom):
            with open(f_nom, mode='r', encoding='utf-8') as f:
                reader = csv.reader(f); next(reader)
                for fila in reader:
                    if len(fila) >= 7:
                        nums = [n.strip() for n in fila[1:7] if n.strip().isdigit()]
                        if len(nums) == 6: dades.append({'Data': fila[0], 'Combinacio': f"[{', '.join(nums)}]", 'Origen': tipus})
    
    with open(FITXER_NETA, 'w', encoding='utf-8', newline='') as f:
        csv.DictWriter(f, fieldnames=['Data', 'Combinacio', 'Origen']).writeheader()
        csv.DictWriter(f, fieldnames=['Data', 'Combinacio', 'Origen']).writerows(dades)

def generar_recomanacio_intel_ligent():
    avui = datetime.now()
    lim_mom = avui - timedelta(days=30)
    lim_biaix = avui - timedelta(days=90)
    stats_mom, stats_hist, triplets_cnt = Counter(), Counter(), Counter()
    sort_mom = 0

    if not os.path.exists(FITXER_NETA): return

    with open(FITXER_NETA, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for fila in reader:
            dt = parsejar_data_flexible(fila['Data'])
            if not dt: continue
            nums = sorted([int(n) for n in fila['Combinacio'].strip('[]').split(',')])
            if dt >= lim_mom:
                sort_mom += 1
                for n in nums: stats_mom[n] += 1
            if dt >= lim_biaix:
                for n in nums: stats_hist[n] += 1
                for t in combinations(nums, 3): triplets_cnt[t] += 1

    scores = []
    top_triplets = [t for t, _ in triplets_cnt.most_common(50)]
    for n in range(1, 50):
        punts = 0
        if stats_mom[n] > (sort_mom * 0.15): punts += 45 
        if stats_hist[n] > 0: punts += (stats_hist[n] * 0.7)
        for t in top_triplets:
            if n in t: punts += 12
        scores.append((n, punts))

    scores.sort(key=lambda x: x[1], reverse=True)
    
    aposta_a = sorted([n for n, p in scores[:6]])
    aposta_b = sorted([n for n, p in scores[6:12]])
    
    # Construïm el missatge per a Telegram
    tiquet = (
        f"🎫 *TIQUET DE JUGADA* - {avui.strftime('%d/%m/%Y')}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎰 *APOSTA PRINCIPAL*\n"
        f"`{' - '.join(f'{n:02d}' for n in aposta_a)}`\n\n"
        f"🎰 *APOSTA SECUNDÀRIA*\n"
        f"`{' - '.join(f'{n:02d}' for n in aposta_b)}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 _Basat en Momentum (30d) i Biaix (90d)_"
    )
    
    # Imprimim per pantalla i enviem a Telegram
    print("\n" + tiquet.replace('*', '').replace('`', ''))
    enviar_telegram(tiquet)

if __name__ == "__main__":
    actualitzar_dades()
    generar_recomanacio_intel_ligent()