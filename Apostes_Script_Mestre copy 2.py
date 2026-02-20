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
                print(f"✅ {nom} descarregat i actualitzat.")
        except: print(f"❌ Error descarregant {nom}. S'usarà la còpia local.")

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
        writer = csv.DictWriter(f, fieldnames=['Data', 'Combinacio', 'Origen'])
        writer.writeheader()
        writer.writerows(dades)
    print(f"✅ Base de dades unificada: {len(dades)} sortejos totals.")

# --- FASE 2: CÀLCUL I IMPRESSIÓ DEL TIQUET ---
def generar_recomanacio_intel_ligent():
    avui = datetime.now()
    lim_mom = avui - timedelta(days=30)
    lim_biaix = avui - timedelta(days=180)

    stats_mom = Counter()
    stats_hist = Counter()
    triplets_cnt = Counter()
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

    # Càlcul de Scores
    scores = []
    top_triplets = [t for t, _ in triplets_cnt.most_common(50)]
    for n in range(1, 50):
        punts = 0
        if stats_mom[n] > (sort_mom * 0.15): punts += 40 
        if stats_hist[n] > 0: punts += (stats_hist[n] * 0.5)
        for t in top_triplets:
            if n in t: punts += 10
        scores.append((n, punts))

    scores.sort(key=lambda x: x[1], reverse=True)
    
    # --- IMPRESSIÓ DEL TIQUET FINAL PER PANTALLA ---
    print("\n" + "═"*45)
    print(f"🎫 TIQUET DE JUGADA RECOMANADA - {avui.strftime('%d/%m/%Y')}")
    print("═"*45)
    
    # Top 12 boles de confiança
    print(f"{'BOLA':<8} | {'PUNTUACIÓ':<10} | {'CONFIANÇA'}")
    print("-" * 45)
    for n, p in scores[:12]:
        estrelles = "⭐" * max(1, int(p/35))
        print(f"Número {n:02d} | {p:9.1f} | {estrelles}")
    
    # Les dues apostes suggerides
    aposta_a = sorted([n for n, p in scores[:6]])
    aposta_b = sorted([n for n, p in scores[6:12]])
    
    print("\n" + "🎰 APOSTA PRINCIPAL (Dades Pures):")
    print(f"👉 {' - '.join(f'{n:02d}' for n in aposta_a)}")
    
    print("\n" + "🎰 APOSTA SECUNDÀRIA (Rerefons):")
    print(f"👉 {' - '.join(f'{n:02d}' for n in aposta_b)}")
    
    print("\n" + "💡 Consell: La 1a aposta combina el millor Momentum")
    print("   amb el biaix estructural més fort.")
    print("═"*45)

if __name__ == "__main__":
    actualitzar_dades()
    generar_recomanacio_intel_ligent()