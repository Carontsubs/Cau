import csv
import os
from collections import Counter
from datetime import datetime, timedelta
import numpy as np
from scipy.stats import pearsonr, spearmanr

FITXER_PRIMI = "Lotoideas.com - Histórico de Resultados - Primitiva - 2013 a 202X(1).csv"
FITXER_BONO = "Lotoideas.com - Histórico de Resultados - Bonoloto - 2013 a 202X(1).csv"

# Cicles reals detectats
CICLE_PRIMI = 297
CICLE_BONO = 251
CICLE_FUSIONAT = 274

# Data últim calibratge (mitjana detectada)
ULTIM_CALIBRATGE = datetime(2025, 7, 22)  # mitjana 05/07 i 28/08/2025


def parsejar_data_flexible(data_str):
    data_netejada = data_str.split(' ')[0].replace('-', '/')
    for fmt in ["%d/%m/%Y", "%Y/%m/%d"]:
        try:
            return datetime.strptime(data_netejada, fmt)
        except:
            continue
    return None


def carregar_frequencies(fitxer, data_inici, data_fi=None):
    """Carrega les freqüències de cada número en un període"""
    freq = Counter()
    sorteigs = 0
    if not os.path.exists(fitxer):
        return freq, sorteigs
    with open(fitxer, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        for fila in reader:
            if len(fila) < 7:
                continue
            nums_raw = [n.strip() for n in fila[1:7] if n.strip().isdigit()]
            if len(nums_raw) != 6:
                continue
            dt = parsejar_data_flexible(fila[0])
            if not dt:
                continue
            if dt < data_inici:
                continue
            if data_fi and dt > data_fi:
                continue
            sorteigs += 1
            for n in nums_raw:
                freq[int(n)] += 1
    return freq, sorteigs


def calcular_correlacio(freq_a, freq_b):
    """Calcula correlació de Pearson i Spearman entre dues distribucions"""
    vec_a = [freq_a[n] for n in range(1, 50)]
    vec_b = [freq_b[n] for n in range(1, 50)]
    pearson_r, pearson_p = pearsonr(vec_a, vec_b)
    spearman_r, spearman_p = spearmanr(vec_a, vec_b)
    return pearson_r, pearson_p, spearman_r, spearman_p


def validar_hipotesi():
    avui = datetime.now()

    print(f"\n{'═'*60}")
    print(f"🔬 VALIDACIÓ HIPÒTESI: BOLES COMPARTIDES")
    print(f"{'═'*60}")
    print(f"   Si Primitiva i Bonoloto comparteixen boles,")
    print(f"   els números freqüents haurien de correlacionar.")
    print(f"{'═'*60}")

    # === CICLE ACTUAL ===
    print(f"\n📊 CICLE ACTUAL (des de {ULTIM_CALIBRATGE.strftime('%d/%m/%Y')}):")
    freq_primi, sort_primi = carregar_frequencies(FITXER_PRIMI, ULTIM_CALIBRATGE)
    freq_bono, sort_bono = carregar_frequencies(FITXER_BONO, ULTIM_CALIBRATGE)

    print(f"   Sorteigs Primitiva: {sort_primi}")
    print(f"   Sorteigs Bonoloto:  {sort_bono}")

    if sort_primi > 5 and sort_bono > 5:
        pr, pp, sr, sp = calcular_correlacio(freq_primi, freq_bono)
        print(f"\n   Correlació de Pearson:  r = {pr:.4f}  (p = {pp:.4f})", end="  →  ")
        interpretar_correlacio(pr, pp)
        print(f"   Correlació de Spearman: r = {sr:.4f}  (p = {sp:.4f})", end="  →  ")
        interpretar_correlacio(sr, sp)

    # === CICLES ANTERIORS ===
    print(f"\n📊 CICLES ANTERIORS (validació històrica):")
    
    # Detecta cicles anteriors aproximats
    cicles_anteriors = []
    data = ULTIM_CALIBRATGE
    for _ in range(5):
        data_fi = data
        data_ini = data - timedelta(days=CICLE_FUSIONAT)
        cicles_anteriors.append((data_ini, data_fi))
        data = data_ini

    print(f"\n   {'CICLE':<30} | {'PEARSON r':<12} | {'SPEARMAN r':<12} | {'INTERPRETACIÓ'}")
    print(f"   {'-'*75}")

    correlacions = []
    for data_ini, data_fi in cicles_anteriors:
        freq_p, sp_p = carregar_frequencies(FITXER_PRIMI, data_ini, data_fi)
        freq_b, sp_b = carregar_frequencies(FITXER_BONO, data_ini, data_fi)
        if sp_p < 5 or sp_b < 5:
            continue
        pr, pp, sr, srp = calcular_correlacio(freq_p, freq_b)
        correlacions.append(pr)
        label = f"{data_ini.strftime('%d/%m/%Y')} → {data_fi.strftime('%d/%m/%Y')}"
        interp = "✅ Correlació" if pr > 0.3 and pp < 0.10 else ("⚠️  Feble" if pr > 0.1 else "❌ Cap")
        print(f"   {label:<30} | {pr:<12.4f} | {sr:<12.4f} | {interp}")

    # === RESUM FINAL ===
    print(f"\n{'═'*60}")
    print(f"📋 RESUM FINAL:")
    if correlacions:
        mitjana_corr = np.mean(correlacions)
        print(f"   Correlació mitjana històrica: {mitjana_corr:.4f}")
        print(f"\n   ", end="")
        if mitjana_corr > 0.3:
            print("✅ HIPÒTESI CONFIRMADA: Les boles semblen compartides.")
            print("      → Usar apostes fusionades és correcte.")
        elif mitjana_corr > 0.1:
            print("⚠️  HIPÒTESI FEBLE: Correlació baixa però positiva.")
            print("      → Fusionar és acceptable però amb precaució.")
        else:
            print("❌ HIPÒTESI REBUTJADA: Les loteries semblen independents.")
            print("      → Millor usar apostes separades per cada loteria.")
    print(f"{'═'*60}")


def interpretar_correlacio(r, p):
    if p < 0.05 and r > 0.3:
        print("✅ Correlació significativa")
    elif p < 0.10 and r > 0.1:
        print("⚠️  Correlació feble")
    else:
        print("❌ Sense correlació")


if __name__ == "__main__":
    validar_hipotesi()