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