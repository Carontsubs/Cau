import csv
import os
import numpy as np
from collections import Counter
from datetime import datetime
from scipy.stats import chisquare

FITXER_PRIMI = "Lotoideas.com - Histórico de Resultados - Primitiva - 2013 a 202X(1).csv"
FITXER_BONO = "Lotoideas.com - Histórico de Resultados - Bonoloto - 2013 a 202X(1).csv"

def parsejar_data_flexible(data_str):
    data_netejada = data_str.split(' ')[0].replace('-', '/')
    for fmt in ["%d/%m/%Y", "%Y/%m/%d"]:
        try:
            return datetime.strptime(data_netejada, fmt)
        except:
            continue
    return None

def carregar_sorteigs(fitxer):
    """Carrega tots els sorteigs d'un CSV ordenats per data"""
    sorteigs = []
    if not os.path.exists(fitxer):
        print(f"❌ No s'ha trobat {fitxer}.")
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

def detectar_calibratges(sorteigs, nom_loteria, finestra=90):
    """Detecta possibles calibratges comparant finestres consecutives"""
    print(f"\n{'═'*60}")
    print(f"🔬 DETECTOR DE CALIBRATGES - {nom_loteria.upper()}")
    print(f"   Total sorteigs: {len(sorteigs)}")
    print(f"   Finestra comparació: {finestra} sorteigs")
    print(f"{'═'*60}")

    resultats = []

    # Llisca una finestra per tota la sèrie
    for i in range(finestra, len(sorteigs) - finestra):
        # Període ABANS
        periode_abans = sorteigs[i - finestra:i]
        # Període DESPRÉS
        periode_despres = sorteigs[i:i + finestra]

        # Freqüències de cada número en cada període
        freq_abans = Counter()
        freq_despres = Counter()
        for _, nums in periode_abans:
            for n in nums:
                freq_abans[n] += 1
        for _, nums in periode_despres:
            for n in nums:
                freq_despres[n] += 1

        # Diferència total entre els dos períodes (distància Manhattan)
        diferencia = sum(abs(freq_abans[n] - freq_despres[n]) for n in range(1, 50))

        data_punt = sorteigs[i][0]
        resultats.append((data_punt, diferencia, i))

    # Troba els pics màxims (possibles calibratges)
    if not resultats:
        print("⚠️  No hi ha prou dades.")
        return

    max_dif = max(r[1] for r in resultats)
    mitjana = sum(r[1] for r in resultats) / len(resultats)

    print(f"\n   Diferència mitjana: {mitjana:.1f}")
    print(f"   Diferència màxima:  {max_dif:.1f}")
    print(f"\n📅 POSSIBLES DATES DE CALIBRATGE (Top 15):")
    print(f"{'DATA':<15} | {'DIFERÈNCIA':<12} | {'INTENSITAT'}")
    print("-" * 55)

    # Filtra pics significatius (per sobre de la mitjana + 1 desviació estàndard)
    std = np.std([r[1] for r in resultats])
    llindar = mitjana + std

    # Evita pics massa propers (mínim 30 sorteigs de distància)
    pics = []
    resultats_ordenats = sorted(resultats, key=lambda x: x[1], reverse=True)
    for data, dif, idx in resultats_ordenats:
        if dif < llindar:
            break
        # Comprova que no sigui massa proper a un pic ja trobat
        if all(abs(idx - p[2]) > 30 for p in pics):
            pics.append((data, dif, idx))
        if len(pics) >= 15:
            break

    # Ordena per data
    pics.sort(key=lambda x: x[0])
    for data, dif, _ in pics:
        intensitat = "🔴 ALT" if dif > mitjana + 2*std else ("🟡 MIG" if dif > llindar else "🟢 BAIX")
        print(f"{data.strftime('%d/%m/%Y'):<15} | {dif:<12.1f} | {intensitat}")

    # Calcula interval mitjà entre calibratges
    if len(pics) >= 2:
        intervals = [(pics[i+1][0] - pics[i][0]).days for i in range(len(pics)-1)]
        interval_mitja = sum(intervals) / len(intervals)
        ultim_calibratge = pics[-1][0]
        proper_estimat = ultim_calibratge + __import__('datetime').timedelta(days=int(interval_mitja))

        print(f"\n📊 RESUM:")
        print(f"   Interval mitjà entre calibratges: {interval_mitja:.0f} dies")
        print(f"   Últim calibratge detectat: {ultim_calibratge.strftime('%d/%m/%Y')}")
        print(f"   Proper calibratge estimat: {proper_estimat.strftime('%d/%m/%Y')}")
        
        dies_restants = (proper_estimat - datetime.now()).days
        if dies_restants > 0:
            print(f"   ⏳ Dies fins al proper calibratge: {dies_restants} dies")
        else:
            print(f"   ⚠️  El calibratge estimat ja hauria d'haver passat fa {abs(dies_restants)} dies!")

    print(f"{'═'*60}")

if __name__ == "__main__":
    sorteigs_primi = carregar_sorteigs(FITXER_PRIMI)
    sorteigs_bono = carregar_sorteigs(FITXER_BONO)

    detectar_calibratges(sorteigs_primi, "Primitiva")
    detectar_calibratges(sorteigs_bono, "Bonoloto")