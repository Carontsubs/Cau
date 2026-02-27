import requests
from bs4 import BeautifulSoup
import csv
import os
from collections import Counter
from itertools import combinations
from datetime import datetime, timedelta
import numpy as np
from scipy.stats import chi2

# 1. CONFIGURACIÓ
FITXER_PRIMI = "Lotoideas.com - Histórico de Resultados - Primitiva - 2013 a 202X(1).csv"
FITXER_BONO = "Lotoideas.com - Histórico de Resultados - Bonoloto - 2013 a 202X(1).csv"
FITXER_APOSTES = "apostes_actuals_separades.csv"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

CICLE_PRIMI, CICLE_BONO = 297, 251
DIES_MOMENTUM_PRIMI, DIES_MOMENTUM_BONO = 30, 25

# 2. FUNCIONS DE SUPORT
def parsejar_data_flexible(data_str):
    data_netejada = data_str.split(' ')[0].replace('-', '/')
    for fmt in ["%d/%m/%Y", "%Y/%m/%d"]:
        try: return datetime.strptime(data_netejada, fmt)
        except: continue
    return None

def carregar_sorteigs(fitxer):
    sorteigs = []
    if not os.path.exists(fitxer): return []
    with open(fitxer, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        for fila in reader:
            if len(fila) < 7: continue
            nums = [n.strip() for n in fila[1:7] if n.strip().isdigit()]
            dt = parsejar_data_flexible(fila[0])
            if dt and len(nums) == 6:
                sorteigs.append((dt, sorted([int(n) for n in nums])))
    sorteigs.sort(key=lambda x: x[0])
    return sorteigs

# 3. ANÀLISI AMB DETALL DE TRIPLETS
def analitzar_loteria(fitxer, nom, d_mom, u_cal):
    sorteigs = carregar_sorteigs(fitxer)
    if not sorteigs: return None, None
    
    # 1. Càlcul de retards (CORREGIT: fem servir r_act i r_max)
    ultim_vist = {n: -1 for n in range(1, 50)}
    r_max = {n: 0 for n in range(1, 50)}
    for idx, (data, nums) in enumerate(sorteigs):
        for n in nums:
            if ultim_vist[n] != -1:
                r = idx - ultim_vist[n] - 1
                if r > r_max[n]: r_max[n] = r
            ultim_vist[n] = idx
    r_act = {n: (len(sorteigs) - ultim_vist[n] - 1) for n in range(1, 50)}

    # 2. Estadístiques de freqüència i Triplets
    lim_mom = datetime.now() - timedelta(days=d_mom)
    stats_mom, stats_hist, triplets = Counter(), Counter(), Counter()
    s_mom, s_hist = 0, 0
    
    for dt, nums in sorteigs:
        if dt >= lim_mom:
            s_mom += 1
            for n in nums: stats_mom[n] += 1
        if dt >= u_cal:
            s_hist += 1
            for n in nums: stats_hist[n] += 1
            for t in combinations(nums, 3):
                triplets[t] += 1

    top_5_triplets = triplets.most_common(5)
    top_trip_boles = [t for t, _ in triplets.most_common(50)]
    
    # 3. Càlcul de Scores
    freq_esp = (s_hist * 6) / 49
    scores = []
    for n in range(1, 50):
        p_hist = stats_hist[n] * 0.8
        p_trip = sum(25 for t in top_trip_boles if n in t)
        
        # Sistema de retards (Ara sí amb r_max i r_act definits)
        p_ret = 150 if (r_max[n] > 0 and (r_act[n]/r_max[n]) >= 0.95) else (60 if (r_max[n] > 0 and (r_act[n]/r_max[n]) > 0.8) else 0)
        
        p_mom = 15 if (s_mom > 0 and stats_mom[n] > (s_mom * 0.15)) else 0
        obs = stats_hist[n]
        chi = ((obs-freq_esp)**2)/freq_esp if freq_esp > 0 else 0
        p_chi = 50 if (1 - chi2.cdf(chi, df=1) < 0.05 and obs > freq_esp) else 0
        
        scores.append({'n': n, 'total': p_hist + p_trip + p_ret + p_mom + p_chi, 'h': p_hist, 't': p_trip, 'r': p_ret, 'm': p_mom, 'c': p_chi})

    scores.sort(key=lambda x: x['total'], reverse=True)
    
    # MOSTRAR DADES PER PANTALLA
    print(f"\n🔥 TRIPLETS MÉS CALENTS - {nom.upper()}:")
    print(f"{'Combinació':<18} | {'Aparicions':<10}")
    print("-" * 35)
    for trip, count in top_5_triplets:
        print(f"{str(trip):<18} | {count} vegades")

    print(f"\n📊 TOP 12 {nom.upper()}:")
    print(f"{'Bola':<6} | {'Hist':<6} | {'Trip':<6} | {'Ret':<6} | {'Mom':<6} | {'Chi':<6} | {'TOTAL':<8}")
    print("-" * 65)
    for s in scores[:12]:
        print(f"{s['n']:02d}     | {s['h']:5.1f} | {s['t']:5.0f} | {s['r']:5.0f} | {s['m']:5.0f} | {s['c']:5.0f} | {s['total']:7.1f}")
    
    return sorted([x['n'] for x in scores[:6]]), sorted([x['n'] for x in scores[6:12]])

if __name__ == "__main__":
    avui = datetime.now()
    data_str = avui.strftime('%d/%m/%Y')

    # Primitiva
    s_p = carregar_sorteigs(FITXER_PRIMI)
    u_p = s_p[-1][0] if s_p else avui
    p_a, p_b = analitzar_loteria(FITXER_PRIMI, "Primitiva", DIES_MOMENTUM_PRIMI, u_p - timedelta(days=90))
    
    # Bonoloto
    s_b = carregar_sorteigs(FITXER_BONO)
    u_b = s_b[-1][0] if s_b else avui
    b_a, b_b = analitzar_loteria(FITXER_BONO, "Bonoloto", DIES_MOMENTUM_BONO, u_b - timedelta(days=90))

    # Tiquet final
    print(f"\n{'━'*45}")
    print(f"🎫 TIQUET GENERAT EL {data_str}")
    print(f"{'━'*45}")
    print(f"🔵 PRIMITIVA:  A: {'-'.join(f'{n:02d}' for n in p_a)} | B: {'-'.join(f'{n:02d}' for n in p_b)}")
    print(f"🟡 BONOLOTO:   A: {'-'.join(f'{n:02d}' for n in b_a)} | B: {'-'.join(f'{n:02d}' for n in b_b)}")
    print(f"{'━'*45}\n")