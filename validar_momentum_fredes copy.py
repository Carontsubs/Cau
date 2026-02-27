import csv
import os
from collections import Counter
from datetime import datetime
import numpy as np
import itertools  # Necessari per als triplets

# CONFIGURACIÓ
FITXER_PRIMI = "Lotoideas.com - Histórico de Resultados - Primitiva - 2013 a 202X(1).csv"
CICLE_PRIMI = 297
MIN_SORTEIGS = 50
FINESTRA_VALIDACIO = 20 

def parsejar_data_flexible(data_str):
    data_netejada = data_str.split(' ')[0].replace('-', '/')
    for fmt in ["%d/%m/%Y", "%Y/%m/%d"]:
        try: return datetime.strptime(data_netejada, fmt)
        except: continue
    return None

def carregar_sorteigs(fitxer):
    sorteigs = []
    if not os.path.exists(fitxer): return sorteigs
    with open(fitxer, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        for fila in reader:
            if len(fila) < 7: continue
            nums_raw = [n.strip() for n in fila[1:7] if n.strip().isdigit()]
            if len(nums_raw) != 6: continue
            dt = parsejar_data_flexible(fila[0])
            if not dt: continue
            sorteigs.append((dt, sorted([int(n) for n in nums_raw])))
    sorteigs.sort(key=lambda x: x[0])
    return sorteigs

def detectar_tots_calibratges(sorteigs, cicle, finestra=90):
    resultats = []
    for i in range(finestra, len(sorteigs) - finestra):
        freq_abans = Counter()
        freq_despres = Counter()
        for _, nums in sorteigs[i - finestra:i]:
            for n in nums: freq_abans[n] += 1
        for _, nums in sorteigs[i:i + finestra]:
            for n in nums: freq_despres[n] += 1
        diferencia = sum(abs(freq_abans[n] - freq_despres[n]) for n in range(1, 50))
        resultats.append((sorteigs[i][0], diferencia, i))
    if not resultats: return []
    mitjana = sum(r[1] for r in resultats) / len(resultats)
    std = np.std([r[1] for r in resultats])
    llindar = mitjana + std
    pics = []
    for data, dif, idx in sorted(resultats, key=lambda x: x[1], reverse=True):
        if dif < llindar: break
        if all(abs(idx - p[2]) > finestra for p in pics):
            pics.append((data, dif, idx))
    pics.sort(key=lambda x: x[0])
    pics_filtrats = []
    for pic in pics:
        if not pics_filtrats or (pic[0] - pics_filtrats[-1][0]).days > cicle // 2:
            pics_filtrats.append(pic)
    return [p[0] for p in pics_filtrats]

def validar_hipotesi_triplets(sorteigs, calibratges):
    print(f"\n{'═'*80}")
    print(f"🔬 VALIDACIÓ: TRIPLETS VS FREQÜÈNCIA INDIVIDUAL (PRIMITIVA)")
    print(f"   Objectiu: Comprovar si les boles de triplets reapareixen més.")
    print(f"{'═'*80}")

    cicles = []
    for i in range(len(calibratges) - 1):
        cicles.append((calibratges[i], calibratges[i + 1]))

    res_trip = []
    res_indiv = []

    print(f"{'CICLE':<25} | {'TRIP Hits %':<12} | {'INDIV Hits %':<12} | {'GUANYA'}")
    print(f"{'-'*75}")

    for d_ini, d_fi in cicles:
        sorteigs_cicle = [(dt, nums) for dt, nums in sorteigs if d_ini <= dt < d_fi]
        if len(sorteigs_cicle) < 100: continue

        # 1. Top 10 individuals
        freq_indiv = Counter(n for _, nums in sorteigs_cicle for n in nums)
        top_indiv = [n for n, _ in freq_indiv.most_common(10)]

        # 2. Top 5 Triplets (Boles que surten juntes)
        triplets_count = Counter()
        for _, nums in sorteigs_cicle:
            for comb in itertools.combinations(nums, 3):
                triplets_count[comb] += 1
        
        millors_triplets = [t[0] for t in triplets_count.most_common(5)]
        boles_triplets = set()
        for t in millors_triplets: boles_triplets.update(t)

        # 3. Validació (seguents 20 sorteigs)
        idx_fi = next((i for i, (dt, _) in enumerate(sorteigs) if dt >= d_fi), None)
        if idx_fi is None or idx_fi + FINESTRA_VALIDACIO > len(sorteigs): continue
        
        nums_futurs = set(n for _, nums in sorteigs[idx_fi:idx_fi + FINESTRA_VALIDACIO] for n in nums)

        pct_trip = (sum(1 for n in boles_triplets if n in nums_futurs) / len(boles_triplets)) * 100
        pct_indiv = (sum(1 for n in top_indiv if n in nums_futurs) / len(top_indiv)) * 100

        res_trip.append(pct_trip)
        res_indiv.append(pct_indiv)

        guanya = "✅ TRIP" if pct_trip > pct_indiv else "❌ INDIV"
        print(f"{d_ini.strftime('%d/%m/%Y')}→{d_fi.strftime('%y/%m/%d'):<8} | {pct_trip:>11.1f}% | {pct_indiv:>12.1f}% | {guanya}")

    if res_trip:
        print(f"{'═'*80}")
        print(f"📊 MITJANA FINAL TRIPLETS:    {np.mean(res_trip):.1f}%")
        print(f"📊 MITJANA FINAL INDIVIDUALS: {np.mean(res_indiv):.1f}%")
        print(f"{'═'*80}")
import csv
import os
from collections import Counter
from datetime import datetime
import numpy as np
import itertools # <--- IMPORTANT: Necessari per als Triplets

# ... (Aquí van les teves funcions de parsejar_data, carregar_sorteigs, etc.) ...

def obtenir_analisi_retards(sorteigs):
    # (El codi que ja tenies per calcular r_act i r_max)
    ultim_vist = {n: -1 for n in range(1, 50)}
    retard_maxim = {n: 0 for n in range(1, 50)}
    for idx, (data, nums) in enumerate(sorteigs):
        for n in nums:
            if ultim_vist[n] != -1:
                r_moment = idx - ultim_vist[n] - 1
                if r_moment > retard_maxim[n]:
                    retard_maxim[n] = r_moment
            ultim_vist[n] = idx
    total_s = len(sorteigs)
    retard_actual = {n: (total_s - ultim_vist[n] - 1) for n in range(1, 50)}
    return retard_actual, retard_maxim

# =========================================================================
# 🚀 AQUÍ HAS DE POSAR LA NOVA FUNCIÓ QUE HEM DISSENYAT
# =================================================)========================
def generar_aposta_mestra(sorteigs, r_act, r_max, nom_loteria):
    ultims_100 = sorteigs[-100:]
    freq = Counter(n for _, nums in ultims_100 for n in nums)
    
    triplets_count = Counter()
    for _, nums in ultims_100:
        for comb in itertools.combinations(nums, 3):
            triplets_count[comb] += 1
    
    punts_triplets = Counter()
    for t, vegades in triplets_count.most_common(10):
        for n in t: punts_triplets[n] += 150
            
    scores = {}
    for n in range(1, 50):
        s = punts_triplets[n] + (freq[n] * 10)
        pct_retard = (r_act[n] / r_max[n]) * 100 if r_max[n] > 0 else 0
        if pct_retard > 85: s += 200 # Bonus de Retard Crític
        scores[n] = s

    critiques = sorted([n for n in range(1, 50) if (r_act[n]/r_max[n] if r_max[n]>0 else 0) > 0.85], 
                       key=lambda x: r_act[x]/r_max[x], reverse=True)[:2]
    restants = sorted([n for n in range(1, 50) if n not in critiques], 
                      key=lambda x: scores[x], reverse=True)[:4]
    
    combinacio = sorted(critiques + restants)
    
    print(f"\n{'═'*70}")
    print(f"🎰 APOSTA MESTRA - {nom_loteria.upper()}")
    print(f"{'═'*70}")
    print(f"👉 NÚMEROS: {', '.join(map(str, sorted(combinacio)))}")
    print(f"{'-'*70}")
    return combinacio

# =========================================================================
# 🏁 BLOC PRINCIPAL D'EXECUCIÓ
# =========================================================================

if __name__ == "__main__":
    s_primi = carregar_sorteigs(FITXER_PRIMI)
    
    if s_primi:
        # 1. Calculem retards
        r_act_p, r_max_p = obtenir_analisi_retards(s_primi)
        
        # 2. Mostrem l'aposta basada en els teus tests (93.4% èxit)
        generar_aposta_mestra(s_primi, r_act_p, r_max_p, "Primitiva")
        
        # 3. (Opcional) També pots cridar l'analitzador de cicles que ja tenies
        # c_primi = detectar_tots_calibratges(s_primi, CICLE_PRIMI)
        # analitzar_distribucio_cicle(s_primi, c_primi, "Primitiva", r_act_p, r_max_p)    
    sorteigs = carregar_sorteigs(FITXER_PRIMI)
    calibratges = detectar_tots_calibratges(sorteigs, CICLE_PRIMI)
    validar_hipotesi_triplets(sorteigs, calibratges)