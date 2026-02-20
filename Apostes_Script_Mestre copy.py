import requests
from bs4 import BeautifulSoup
import csv
import os
from collections import Counter
from itertools import combinations
from datetime import datetime, timedelta

# === CONFIGURACIÓ GLOBAL ===
FITXER_PRIMI = "Lotoideas.com - Histórico de Resultados - Primitiva - 2013 a 202X(1).csv"
FITXER_BONO = "Lotoideas.com - Histórico de Resultados - Bonoloto - 2013 a 202X(1).csv"
FITXER_NETA = "estadistiques_loteries_NETA.csv"
HEADERS = {'User-Agent': 'Mozilla/5.0'}

def parsejar_data_flexible(data_str):
    data_netejada = data_str.split(' ')[0].replace('-', '/')
    for fmt in ["%d/%m/%Y", "%Y/%m/%d"]:
        try: return datetime.strptime(data_netejada, fmt)
        except: continue
    return None

# --- FASE 1: DESCÀRREGA I FUSIÓ ---
def actualitzar_dades():
    print("🛰️  FASE 1: ACTUALITZANT DADES...")
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
                print(f"✅ {nom} OK.")
        except: print(f"❌ Error a {nom}")

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

# --- FASE 2: CÀLCUL DE SCORES (L'ENCREUAMENT) ---
def generar_recomanacio_intel_ligent():
    avui = datetime.now()
    # 1. Momentum (30 dies)
    lim_mom = avui - timedelta(days=30)
    # 2. Biaix Estructural (Triplets de 180 dies)
    lim_biaix = avui - timedelta(days=180)

    stats_mom = Counter()
    stats_hist = Counter()
    triplets_cnt = Counter()
    sort_mom = 0

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

    # Càlcul de punts per cada bola (1-49)
    scores = []
    top_triplets = [t for t, _ in triplets_cnt.most_common(50)]
    
    for n in range(1, 50):
        punts = 0
        # Punts per Momentum (Si està en ratxa)
        if stats_mom[n] > (sort_mom * 0.15): punts += 40 
        # Punts per Biaix Històric (Si és consistent)
        if stats_hist[n] > 0: punts += (stats_hist[n] * 0.5)
        # Punts per Triplets (Si forma part dels millors grups)
        for t in top_triplets:
            if n in t: punts += 10
        
        scores.append((n, punts))

    scores.sort(key=lambda x: x[1], reverse=True)

    print("\n" + "💎"*20)
    print("🎯 CALCULADORA DE PROBABILITAT FINAL")
    print("Encreuant Momentum (30d) + Biaix (180d)")
    print("💎"*20)
    print(f"{'BOLA':<8} | {'PUNTUACIÓ DE CONFIANÇA'}")
    print("-" * 35)
    for n, p in scores[:12]:
        estrelles = "⭐" * int(p/30)
        print(f"Número {n:02d} | {p:6.1f} {estrelles}")
    
    recomanada = [str(n) for n, p in scores[:6]]
    print("\n" + "═"*40)
    print(f"🎰 JUGADA MESTRA SUGGERIDA: {' - '.join(recomanada)}")
    print("═"*40)

if __name__ == "__main__":
    actualitzar_dades()
    generar_recomanacio_intel_ligent()