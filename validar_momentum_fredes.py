import csv
import os
from collections import Counter
from datetime import datetime
import numpy as np
from scipy.stats import chisquare

FITXER_PRIMI = "Lotoideas.com - Histórico de Resultados - Primitiva - 2013 a 202X(1).csv"

CICLE_PRIMI = 297
MIN_SORTEIGS = 50
MAX_SORTEIGS = 500
FINESTRA_MOMENTUM = 10
FINESTRA_VALIDACIO = 5  # sorteigs posteriors per comprovar si surten


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
            if len(fila) < 7:
                continue
            nums_raw = [n.strip() for n in fila[1:7] if n.strip().isdigit()]
            if len(nums_raw) != 6:
                continue
            dt = parsejar_data_flexible(fila[0])
            if not dt:
                continue
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

    if not resultats:
        return []

    mitjana = sum(r[1] for r in resultats) / len(resultats)
    std = np.std([r[1] for r in resultats])
    llindar = mitjana + std

    pics = []
    for data, dif, idx in sorted(resultats, key=lambda x: x[1], reverse=True):
        if dif < llindar:
            break
        if all(abs(idx - p[2]) > finestra for p in pics):
            pics.append((data, dif, idx))
        if len(pics) >= 20:
            break

    pics.sort(key=lambda x: x[0])
    pics_filtrats = []
    for pic in pics:
        if not pics_filtrats or (pic[0] - pics_filtrats[-1][0]).days > cicle // 2:
            pics_filtrats.append(pic)

    return [p[0] for p in pics_filtrats]


def classificar_fredes(sorteigs_cicle, fredes):
    """Classifica les boles fredes en COMPENSANT vs CONGELADA"""
    ultims = sorteigs_cicle[-FINESTRA_MOMENTUM:]
    freq_recent = Counter()
    for _, nums in ultims:
        for n in nums:
            freq_recent[n] += 1
    esperanca = (FINESTRA_MOMENTUM * 6) / 49

    compensant = []
    congelada = []
    for n in fredes:
        if freq_recent[n] > esperanca * 1.5:
            compensant.append(n)
        elif freq_recent[n] > 0:
            compensant.append(n)  # despertant també compta com compensant
        else:
            congelada.append(n)

    return compensant, congelada


def validar_hipotesi_momentum(sorteigs, calibratges):
    """Per cada cicle, comprova si les boles COMPENSANT surten més als 20 sorteigs següents"""

    print(f"\n{'═'*70}")
    print(f"🔬 VALIDACIÓ: COMPENSANT vs CONGELADA")
    print(f"   Hipòtesi: boles fredes COMPENSANT surten més als {FINESTRA_VALIDACIO} sorteigs")
    print(f"   posteriors que les CONGELADES")
    print(f"{'═'*70}")

    # Construeix cicles
    cicles = []
    for i in range(len(calibratges) - 1):
        cicles.append((calibratges[i], calibratges[i + 1]))

    resultats_comp = []   # % aparicions de boles COMPENSANT
    resultats_cong = []   # % aparicions de boles CONGELADES

    print(f"\n{'CICLE':<25} | {'COMP surten':<12} | {'CONG surten':<12} | {'COMP > CONG'}")
    print(f"{'-'*65}")

    for data_ini, data_fi in cicles:
        sorteigs_cicle = [(dt, nums) for dt, nums in sorteigs
                         if dt >= data_ini and dt < data_fi]

        if len(sorteigs_cicle) < MIN_SORTEIGS + FINESTRA_MOMENTUM + FINESTRA_VALIDACIO:
            continue

        # Calcula freqüències del cicle per detectar fredes
        freq = Counter()
        for _, nums in sorteigs_cicle:
            for n in nums:
                freq[n] += 1
        freq_esperada = (len(sorteigs_cicle) * 6) / 49
        fredes = [n for n in range(1, 50) if freq[n] < freq_esperada * 0.75]

        if not fredes:
            continue

        # Classifica fredes als últims 10 sorteigs del cicle
        compensant, congelada = classificar_fredes(sorteigs_cicle, fredes)

        if not compensant or not congelada:
            continue

        # Troba els 20 sorteigs POSTERIORS al cicle (inici del cicle següent)
        idx_fi = next((i for i, (dt, _) in enumerate(sorteigs) if dt >= data_fi), None)
        if idx_fi is None or idx_fi + FINESTRA_VALIDACIO > len(sorteigs):
            continue

        sorteigs_validacio = sorteigs[idx_fi:idx_fi + FINESTRA_VALIDACIO]
        nums_validacio = set()
        for _, nums in sorteigs_validacio:
            nums_validacio.update(nums)

        # Calcula % de cada grup que surt
        comp_surten = sum(1 for n in compensant if n in nums_validacio)
        cong_surten = sum(1 for n in congelada if n in nums_validacio)

        pct_comp = comp_surten / len(compensant) * 100
        pct_cong = cong_surten / len(congelada) * 100

        resultats_comp.append(pct_comp)
        resultats_cong.append(pct_cong)

        guanya = "✅" if pct_comp > pct_cong else "❌"
        label = f"{data_ini.strftime('%d/%m/%Y')} → {data_fi.strftime('%d/%m/%Y')}"
        print(f"{label:<25} | {pct_comp:>8.1f}%   | {pct_cong:>8.1f}%   | {guanya}")

    # Resum final
    if resultats_comp:
        mitjana_comp = np.mean(resultats_comp)
        mitjana_cong = np.mean(resultats_cong)
        victores = sum(1 for c, g in zip(resultats_comp, resultats_cong) if c > g)
        total = len(resultats_comp)

        print(f"\n{'═'*70}")
        print(f"📊 RESUM FINAL:")
        print(f"   Mitjana COMPENSANT: {mitjana_comp:.1f}%")
        print(f"   Mitjana CONGELADA:  {mitjana_cong:.1f}%")
        print(f"   Cicles on COMP > CONG: {victores}/{total} ({victores/total*100:.1f}%)")
        print(f"\n   ", end="")
        if victores / total > 0.60:
            print("✅ HIPÒTESI CONFIRMADA: COMPENSANT surten més que CONGELADES!")
            print("      → Té sentit prioritzar boles COMPENSANT al model")
        elif victores / total > 0.50:
            print("⚠️  HIPÒTESI FEBLE: Lleuger avantatge de COMPENSANT")
        else:
            print("❌ HIPÒTESI REBUTJADA: COMPENSANT no surten més que CONGELADES")
            print("      → No afegeix valor al model")
        print(f"{'═'*70}")


if __name__ == "__main__":
    print("🔬 VALIDACIÓ HIPÒTESI MOMENTUM DE BOLES FREDES - PRIMITIVA")
    print(f"   Finestra momentum: {FINESTRA_MOMENTUM} sorteigs")
    print(f"   Finestra validació: {FINESTRA_VALIDACIO} sorteigs posteriors")

    sorteigs = carregar_sorteigs(FITXER_PRIMI)
    calibratges = detectar_tots_calibratges(sorteigs, CICLE_PRIMI)

    print(f"   Calibratges detectats: {len(calibratges)}")

    validar_hipotesi_momentum(sorteigs, calibratges)
