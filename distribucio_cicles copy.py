import csv
import os
from collections import Counter
from datetime import datetime
import numpy as np
from scipy.stats import chisquare

# CONFIGURACIÓ
FITXER_PRIMI = "Lotoideas.com - Histórico de Resultados - Primitiva - 2013 a 202X(1).csv"
FITXER_BONO = "Lotoideas.com - Histórico de Resultados - Bonoloto - 2013 a 202X(1).csv"

CICLE_PRIMI = 297
CICLE_BONO = 251
MIN_SORTEIGS = 50
MAX_SORTEIGS = 500
FINESTRA_MOMENTUM = 10 

def parsejar_data_flexible(data_str):
    data_netejada = data_str.split(' ')[0].replace('-', '/')
    for fmt in ["%d/%m/%Y", "%Y/%m/%d"]:
        try:
            return datetime.strptime(data_netejada, fmt)
        except:
            continue
    return None

def carregar_sorteigs(fitxer):
    sorteigs = []
    if not os.path.exists(fitxer):
        return sorteigs
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
        if len(pics) >= 20: break
    pics.sort(key=lambda x: x[0])
    pics_filtrats = []
    for pic in pics:
        if not pics_filtrats or (pic[0] - pics_filtrats[-1][0]).days > cicle // 2:
            pics_filtrats.append(pic)
    return [p[0] for p in pics_filtrats]

def obtenir_analisi_retards(sorteigs):
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

def analitzar_momentum(ca_sorteigs, fredes):
    ultims = ca_sorteigs[-FINESTRA_MOMENTUM:]
    freq_recent = Counter()
    for _, nums in ultims:
        for n in nums: freq_recent[n] += 1
    esperanca = (FINESTRA_MOMENTUM * 6) / 49
    print(f"\n🚀 ANÀLISI DE MOMENTUM (Últims {FINESTRA_MOMENTUM} sorteigs):")
    print(f"   {'Bola':<5} | {'Freq Cicle':<10} | {'Recent':<7} | {'Estat'}")
    print(f"   {'-'*45}")
    for n in fredes:
        f_r = freq_recent[n]
        status = "💤 Congelada"
        if f_r > esperanca * 1.5: status = "⚡ COMPENSANT!"
        elif f_r > 0: status = "📈 Despertant"
        
        # Comptem quantes vegades ha sortit en el cicle actual
        count_cicle = sum(1 for _, nums in ca_sorteigs if n in nums)
        print(f"   {n:<5} | {count_cicle:<10} | {f_r:<7} | {status}")

def analitzar_distribucio_cicle(sorteigs, calibratges, nom_loteria, r_act, r_max):
    print(f"\n{'═'*70}")
    print(f"📊 ESTRATÈGIA DE CICLES - {nom_loteria.upper()}")
    print(f"{'═'*70}")
    data_ini = calibratges[-1]
    sorteigs_cicle = [(dt, nums) for dt, nums in sorteigs if dt >= data_ini]
    freq = Counter()
    for _, nums in sorteigs_cicle:
        for n in nums: freq[n] += 1
    total_s = len(sorteigs_cicle)
    f_esp = (total_s * 6) / 49
    observades = [freq[n] for n in range(1, 50)]
    _, p_v = chisquare(observades)
    fredes = sorted([n for n in range(1, 50) if freq[n] < f_esp * 0.75], key=lambda x: freq[x])
    
    print(f"📅 CICLE ACTUAL: {data_ini.strftime('%d/%m/%Y')} → Avui ({total_s} sorteigs)")
    print(f"📊 P-valor de distribució: {p_v:.4f}")
    
    if fredes:
        analitzar_momentum(sorteigs_cicle, fredes)
    
    print("\n🔥 FILTRE DE RETARD CRÍTIC (Probabilitat de trencament):")
    for n in range(1, 50):
        percentatge = (r_act[n] / r_max[n]) * 100 if r_max[n] > 0 else 0
        if percentatge > 85:
            print(f"   Bola {n}: Actual {r_act[n]} | Màxim {r_max[n]} ({percentatge:.1f}%) -> 🔥 CRÍTIC")
    print(f"{'═'*70}")

# --- BLOC PRINCIPAL CORREGIT ---
if __name__ == "__main__":
    # Carreguem dades
    s_primi = carregar_sorteigs(FITXER_PRIMI)
    s_bono = carregar_sorteigs(FITXER_BONO)
    
    # Processament Primitiva
    if s_primi:
        r_act_p, r_max_p = obtenir_analisi_retards(s_primi)
        c_primi = detectar_tots_calibratges(s_primi, CICLE_PRIMI)
        analitzar_distribucio_cicle(s_primi, c_primi, "Primitiva", r_act_p, r_max_p)

    # Processament Bonoloto
    if s_bono:
        r_act_b, r_max_b = obtenir_analisi_retards(s_bono)
        c_bono = detectar_tots_calibratges(s_bono, CICLE_BONO)
        analitzar_distribucio_cicle(s_bono, c_bono, "Bonoloto", r_act_b, r_max_b)