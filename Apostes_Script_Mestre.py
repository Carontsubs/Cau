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
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

# === FUNCIONS AUXILIARS ===
def parsejar_data_flexible(data_str):
    data_netejada = data_str.split(' ')[0].replace('-', '/')
    formats = ["%d/%m/%Y", "%Y/%m/%d"]
    for fmt in formats:
        try:
            return datetime.strptime(data_netejada, fmt)
        except ValueError:
            continue
    return None

# === FASE 1: DESCARREGA I FUSIÓ ===
def actualitzar_i_fusionar():
    print("\n" + "═"*50)
    print("🛰️  FASE 1: ACTUALITZACIÓ DE DADES")
    print("═"*50)
    tasques = [
        ("https://www.lotoideas.com/primitiva-resultados-historicos-de-todos-los-sorteos/", FITXER_PRIMI, "gid=1"),
        ("https://www.lotoideas.com/bonoloto-resultados-historicos-de-todos-los-sorteos/", FITXER_BONO, "gid=0")
    ]

    for url_web, nom_desti, gid_clau in tasques:
        try:
            r = requests.get(url_web, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            enllaç = next((a['href'] for a in soup.find_all('a', href=True) if "output=csv" in a['href'] and gid_clau in a['href']), None)
            if enllaç:
                contingut = requests.get(enllaç, headers=HEADERS).content
                with open(nom_desti, 'wb') as f: f.write(contingut)
                print(f"✅ {nom_desti} actualitzat.")
        except Exception as e: print(f"❌ Error descarregant {nom_desti}: {e}")

    print("\n🔄 FUSIONANT HISTÒRIALS EN UN ÚNIC FITXER...")
    dades_totals = []
    for fitxer, tipus in [(FITXER_PRIMI, "Primitiva"), (FITXER_BONO, "Bonoloto")]:
        if os.path.exists(fitxer):
            with open(fitxer, mode='r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)
                for fila in reader:
                    if len(fila) < 7: continue
                    nums = [n.strip() for n in fila[1:7] if n.strip().isdigit()]
                    if len(nums) == 6:
                        dades_totals.append({'Data': fila[0].strip(), 'Combinacio': f"[{', '.join(nums)}]", 'Origen': tipus})
    
    with open(FITXER_NETA, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Data', 'Combinacio', 'Origen'])
        writer.writeheader()
        writer.writerows(dades_totals)
    print(f"✅ Fusió completada: {len(dades_totals)} sortejos analitzables.\n")

# === FASE 2: DETECTOR D'EXPLOSIÓ (MOMENTUM) ===
def analitzar_momentum():
    print("🚀" * 20)
    print("🔍 FASE 2: DETECTOR D'EXPLOSIÓ (MOMENTUM 30 DIES)")
    print("-" * 55)
    avui = datetime.now()
    limit_present = avui - timedelta(days=30)
    limit_passat = avui - timedelta(days=180)

    stats_present, stats_passat = Counter(), Counter()
    sortejos_present, sortejos_passat = 0, 0

    if not os.path.exists(FITXER_NETA): return

    with open(FITXER_NETA, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for fila in reader:
            dt = parsejar_data_flexible(fila['Data'])
            if not dt: continue
            nums = [int(n) for n in fila['Combinacio'].strip('[]').split(',')]
            
            if dt >= limit_present:
                sortejos_present += 1
                for n in nums: stats_present[n] += 1
            elif limit_present > dt >= limit_passat:
                sortejos_passat += 1
                for n in nums: stats_passat[n] += 1

    if sortejos_present > 0 and sortejos_passat > 0:
        creixement = []
        for n in range(1, 50):
            f_pres = (stats_present[n] / sortejos_present) * 100
            f_pass = (stats_passat[n] / sortejos_passat) * 100
            creixement.append((n, f_pass, f_pres, f_pres - f_pass))
        
        creixement.sort(key=lambda x: x[3], reverse=True)
        for n, f_v, f_n, diff in creixement[:10]:
            print(f"BOLA {n:02d} | ABANS: {f_v:4.1f}% | ARA: {f_n:4.1f}% | CREIXEMENT: +{diff:4.1f}% 🔥")
    else:
        print("⚠️ No hi ha prou sortejos recents per calcular el Momentum.")
    print("🚀" * 20 + "\n")

# === FASE 3: ANÀLISI DE BIAIX (TRIPLETS AMB FILTRE PERSONALITZAT) ===
def analitzar_triplets():
    print("═" * 50)
    print("📊 FASE 3: ANÀLISI DE BIAIX ESTRUCTURAL (TRIPLETS)")
    print("═" * 50)
    print("1. Tota l'estadística")
    print("2. Últim any (365 dies)")
    print("3. Últims 6 mesos (180 dies)")
    print("4. INTRODUIR DIES ENRERE MANUALMENT")
    
    opcio = input("\nTria el període per als Triplets: ")
    limit_data = None
    avui = datetime.now()

    if opcio == '2':
        limit_data = avui - timedelta(days=365)
    elif opcio == '3':
        limit_data = avui - timedelta(days=180)
    elif opcio == '4':
        try:
            n_dies = int(input("Quants dies enrere vols analitzar? "))
            limit_data = avui - timedelta(days=n_dies)
        except ValueError:
            print("Valor no vàlid. S'analitzarà tota l'estadística.")

    triplets_cnt = Counter()
    total_sortejos = 0

    with open(FITXER_NETA, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for fila in reader:
            dt = parsejar_data_flexible(fila['Data'])
            if limit_data and (not dt or dt < limit_data): continue
            
            nums = sorted([int(n) for n in fila['Combinacio'].strip('[]').split(',')])
            for t in combinations(nums, 3):
                triplets_cnt[t] += 1
            total_sortejos += 1

    if total_sortejos == 0:
        print("❌ No s'han trobat sortejos en el període seleccionat.")
        return

    # Probabilitat teòrica (Aprox. 1 cada 921 sortejos per cada combinació de 3)
    prob_teorica = 20 / 18424
    ranking = sorted(triplets_cnt.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\n📈 RESULTATS (Sortejos analitzats: {total_sortejos}):")
    print(f"{'TRIPLET':<18} | {'COPS':<5} | {'FREQ':<7} | {'MULTIPLICADOR'}")
    print("-" * 55)
    
    for t, cops in ranking[:20]:
        freq_real = cops / total_sortejos
        mult = freq_real / prob_teorica
        foc = "🔥" if mult >= 2 else ""
        print(f"{str(list(t)):<18} | {cops:<5} | {freq_real*100:5.2f}% | {mult:6.2f}x {foc}")

# === EXECUCIÓ PRINCIPAL ===
if __name__ == "__main__":
    actualitzar_i_fusionar()
    analitzar_momentum()
    analitzar_triplets()
    print("\n✅ Procés finalitzat. Bona sort!")