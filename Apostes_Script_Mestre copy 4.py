import requests
from bs4 import BeautifulSoup
import csv
import os
from collections import Counter
from itertools import combinations
from datetime import datetime, timedelta
import math
from scipy.stats import chisquare
from scipy.stats import chi2


# === CONFIGURACIÓ GLOBAL ===
FITXER_PRIMI = "Lotoideas.com - Histórico de Resultados - Primitiva - 2013 a 202X(1).csv"
FITXER_BONO = "Lotoideas.com - Histórico de Resultados - Bonoloto - 2013 a 202X(1).csv"
FITXER_NETA = "estadistiques_loteries_NETA.csv"
HEADERS = {'User-Agent': 'Mozilla/5.0'}

def parsejar_data_flexible(data_str):
    """Parseja dates en formats flexibles"""
    data_netejada = data_str.split(' ')[0].replace('-', '/')
    for fmt in ["%d/%m/%Y", "%Y/%m/%d"]:
        try:
            return datetime.strptime(data_netejada, fmt)
        except:
            continue
    return None

# --- FASE 1: DESCÀRREGA I FUSIÓ ---
def actualitzar_dades():
    """Descarrega les dades més recents de lotoideas.com"""
    print("🛰️  FASE 1: ACTUALITZANT DADES DES DE LA WEB...")
    tasques = [
        ("https://www.lotoideas.com/primitiva-resultados-historicos-de-todos-los-sorteos/", FITXER_PRIMI, "gid=1"),
        ("https://www.lotoideas.com/bonoloto-resultados-historicos-de-todos-los-sorteos/", FITXER_BONO, "gid=0")
    ]
    
    for url, nom, gid in tasques:
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            link = next((a['href'] for a in soup.find_all('a', href=True) 
                        if "output=csv" in a['href'] and gid in a['href']), None)
            if link:
                with open(nom, 'wb') as f:
                    f.write(requests.get(link).content)
                print(f"✅ {nom} descarregat i actualitzat.")
        except Exception as e:
            print(f"❌ Error descarregant {nom}. S'usarà la còpia local.")

    # Fusiona Primitiva i Bonoloto
    dades = []
    for f_nom, tipus in [(FITXER_PRIMI, "Primitiva"), (FITXER_BONO, "Bonoloto")]:
        if os.path.exists(f_nom):
            with open(f_nom, mode='r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # Salta capçalera
                for fila in reader:
                    if len(fila) >= 7:
                        nums = [n.strip() for n in fila[1:7] if n.strip().isdigit()]
                        if len(nums) == 6:
                            dades.append({
                                'Data': fila[0],
                                'Combinacio': f"[{', '.join(nums)}]",
                                'Origen': tipus
                            })
    
    # Escriu la base de dades unificada
    with open(FITXER_NETA, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Data', 'Combinacio', 'Origen'])
        writer.writeheader()
        writer.writerows(dades)
    
    print(f"✅ Base de dades unificada: {len(dades)} sortejos totals.")

# --- FASE 2: CÀLCUL I IMPRESSIÓ DEL TIQUET ---

def generar_recomanacio_intel_ligent():
    """Analitza dades i genera recomanació basada en biaix mecànic"""
    avui = datetime.now()
    lim_mom = avui - timedelta(days=30)
    lim_biaix = avui - timedelta(days=90)

    stats_mom = Counter()
    stats_hist = Counter()
    triplets_cnt = Counter()
    sort_mom = 0
    sort_biaix = 0

    if not os.path.exists(FITXER_NETA):
        print("❌ No s'ha trobat la base de dades. Executa actualitzar_dades() primer.")
        return

    with open(FITXER_NETA, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for fila in reader:
            dt = parsejar_data_flexible(fila['Data'])
            if not dt:
                continue
            nums = sorted([int(n) for n in fila['Combinacio'].strip('[]').split(',')])
            if dt >= lim_mom:
                sort_mom += 1
                for n in nums:
                    stats_mom[n] += 1
            if dt >= lim_biaix:
                sort_biaix += 1
                for n in nums:
                    stats_hist[n] += 1
                for t in combinations(nums, 3):
                    triplets_cnt[t] += 1

    # --- TEST CHI-QUADRAT ---
    # Freqüència esperada: si fos perfectament aleatori, cada número hauria de sortir
    # (sort_biaix * 6) / 49 vegades
    freq_esperada = (sort_biaix * 6) / 49
    observades = [stats_hist[n] for n in range(1, 50)]
    _, p_valor_global = chisquare(observades)
    
    # P-valor per número individual: compara cada número contra l'esperat
    significatius = {}
    for n in range(1, 50):
        obs = stats_hist[n]
        # Chi-quadrat simplificat per 1 número: (obs - esp)² / esp
        chi_n = ((obs - freq_esperada) ** 2) / freq_esperada
        # Convertim a p-valor aproximat (1 grau de llibertat)
        p_n = 1 - chi2.cdf(chi_n, df=1)
        significatius[n] = {
            'obs': obs,
            'esp': freq_esperada,
            'chi': chi_n,
            'p': p_n,
            'desviacio': obs - freq_esperada  # positiu = surt més del normal
        }

    # --- CÀLCUL DE SCORES ---
    scores = []
    top_triplets = [t for t, _ in triplets_cnt.most_common(50)]

    print("\n📊 DESGLOSSAT DE PUNTUACIÓ (Top 12):")
    print("=" * 100)
    print(f"{'BOLA':<8} | {'MOMENTUM':<10} | {'BIAIX':<10} | {'TRIPLETS':<10} | {'CHI p-val':<12} | {'SIGNIFICAT':<12} | {'TOTAL':<10}")
    print("-" * 100)

    for n in range(1, 50):
        punts = 0
        punts_mom = 0
        punts_hist = 0
        punts_trip = 0
        punts_chi = 0

        if stats_mom[n] > (sort_mom * 0.15):
            punts_mom = 40
            punts += 40

        if stats_hist[n] > 0:
            punts_hist = stats_hist[n] * 0.5
            punts += punts_hist

        for t in top_triplets:
            if n in t:
                punts_trip += 10
        punts += punts_trip

        # Bonus chi-quadrat:
        # Si p < 0.05 i surt MÉS del normal → bonus +50
        # Si p < 0.10 i surt MÉS del normal → bonus +25
        # Si surt MENYS del normal → penalització
        p_n = significatius[n]['p']
        desv = significatius[n]['desviacio']
        
        if desv > 0:  # Surt més del normal
            if p_n < 0.05:
                punts_chi = 50
            elif p_n < 0.10:
                punts_chi = 25
        else:  # Surt menys del normal → penalitza
            if p_n < 0.05:
                punts_chi = -50
            elif p_n < 0.10:
                punts_chi = -25
        
        punts += punts_chi
        scores.append((n, punts, punts_mom, punts_hist, punts_trip, punts_chi, p_n, desv))

    scores.sort(key=lambda x: x[1], reverse=True)

    for n, total, mom, hist, trip, chi, p_n, desv in scores[:12]:
        signe = "🔺 SOBRE" if desv > 0 else "🔻 SOTA"
        sig = "✅ SÍ" if p_n < 0.10 else "❌ NO"
        print(f"Número {n:02d} | {mom:9.1f} | {hist:9.1f} | {trip:9.1f} | {p_n:11.4f} | {sig:<12} | {total:9.1f}  {signe}")

    print("=" * 100)
    print(f"\n🔬 TEST CHI-QUADRAT GLOBAL (90 dies, {sort_biaix} sorteigs):")
    print(f"   p-valor global = {p_valor_global:.4f}", end="  →  ")
    if p_valor_global < 0.05:
        print("✅ Biaix estadísticament SIGNIFICATIU (p < 0.05) → Hi ha senyal real!")
    elif p_valor_global < 0.10:
        print("⚠️  Biaix MARGINAL (p < 0.10) → Possible senyal, prudència.")
    else:
        print("❌ Sense biaix significatiu → Probablement soroll aleatori.")

    # --- TIQUET FINAL ---
    print("\n" + "═"*60)
    print(f"🎫 TIQUET DE JUGADA RECOMANADA - {avui.strftime('%d/%m/%Y')}")
    print("═"*60)

    print(f"\n{'BOLA':<8} | {'PUNTUACIÓ':<12} | {'CHI':<8} | {'CONFIANÇA'}")
    print("-" * 60)
    for n, p, _, _, _, chi, p_n, desv in scores[:12]:
        estrelles = "⭐" * max(1, int(p/35))
        sig = "✅" if p_n < 0.10 else "  "
        print(f"Número {n:02d} | {p:11.1f} | {sig}     | {estrelles}")

    aposta_a = sorted([n for n, _, _, _, _, _, _, _ in scores[:6]])
    aposta_b = sorted([n for n, _, _, _, _, _, _, _ in scores[6:12]])

    print("\n🎰 APOSTA PRINCIPAL (Dades Pures):")
    print(f"👉 {' - '.join(f'{n:02d}' for n in aposta_a)}")
    print("\n🎰 APOSTA SECUNDÀRIA (Rerefons):")
    print(f"👉 {' - '.join(f'{n:02d}' for n in aposta_b)}")

    print("\n💡 CONSELLS:")
    print("   • ✅ = número amb desviació estadísticament significativa (p < 0.10).")
    print("   • Si el p-valor global és > 0.10, les apostes són de baixa confiança.")
    print("   • No és garantia de guany, només probabilitat estadística.")
    print("═"*60)

    print("\n📈 ESTADÍSTIQUES GENERALS:")
    print(f"   • Sorteigs analitzats (últims 30 dies): {sort_mom}")
    print(f"   • Sorteigs analitzats (últims 90 dies): {sort_biaix}")
    print(f"   • Freqüència esperada per número: {freq_esperada:.1f} aparicions")
    print(f"   • Números més comuns (90 dies): {', '.join(f'{n}' for n, _ in stats_hist.most_common(5))}")
    print(f"   • Números menys comuns (90 dies): {', '.join(f'{n}' for n, _ in stats_hist.most_common()[-5:])}")
if __name__ == "__main__":
    actualitzar_dades()
    generar_recomanacio_intel_ligent()
