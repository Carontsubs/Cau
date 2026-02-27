import csv
import os
from collections import Counter
from datetime import datetime, timedelta
import numpy as np
from scipy.stats import chisquare, norm

FITXER_PRIMI = "Lotoideas.com - Histórico de Resultados - Primitiva - 2013 a 202X(1).csv"
FITXER_BONO = "Lotoideas.com - Histórico de Resultados - Bonoloto - 2013 a 202X(1).csv"

CICLE_PRIMI = 297
CICLE_BONO = 251

# Dates de calibratge detectades pel detector
CALIBRATGES_PRIMI = [
    datetime(2014, 2, 15),
    datetime(2015, 6, 27),
    datetime(2016, 4, 14),
    datetime(2016, 8, 25),
    datetime(2018, 4, 7),
    datetime(2018, 11, 15),
    datetime(2019, 3, 2),
    datetime(2019, 10, 26),
    datetime(2021, 1, 2),
    datetime(2022, 3, 26),
    datetime(2022, 7, 11),
    datetime(2023, 9, 28),
    datetime(2024, 9, 28),
    datetime(2025, 2, 20),
    datetime(2025, 7, 5),
]

CALIBRATGES_BONO = [
    datetime(2016, 1, 16),
    datetime(2016, 3, 29),
    datetime(2016, 5, 4),
    datetime(2018, 2, 28),
    datetime(2018, 6, 15),
    datetime(2018, 9, 28),
    datetime(2021, 10, 15),
    datetime(2022, 10, 28),
    datetime(2023, 5, 21),
    datetime(2023, 9, 7),
    datetime(2024, 5, 22),
    datetime(2024, 7, 2),
    datetime(2024, 8, 19),
    datetime(2024, 11, 14),
    datetime(2025, 8, 28),
]


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


def analitzar_distribucio_cicle(sorteigs, calibratges, nom_loteria):
    """Analitza la distribució de boles dins de cada cicle de calibratge"""
    print(f"\n{'═'*70}")
    print(f"📊 DISTRIBUCIÓ DE BOLES PER CICLE - {nom_loteria.upper()}")
    print(f"{'═'*70}")

    # Afegeix data actual com a fi de l'últim cicle
    cicles = []
    for i in range(len(calibratges) - 1):
        cicles.append((calibratges[i], calibratges[i+1]))
    cicles.append((calibratges[-1], datetime.now()))

    resultats_cicles = []

    for data_ini, data_fi in cicles:
        # Filtra sorteigs del cicle
        sorteigs_cicle = [(dt, nums) for dt, nums in sorteigs
                         if dt >= data_ini and dt < data_fi]

        if len(sorteigs_cicle) < 20:
            continue

        # Calcula freqüències
        freq = Counter()
        for _, nums in sorteigs_cicle:
            for n in nums:
                freq[n] += 1

        total_sorteigs = len(sorteigs_cicle)
        freq_esperada = (total_sorteigs * 6) / 49

        # Chi-quadrat del cicle
        observades = [freq[n] for n in range(1, 50)]
        _, p_valor = chisquare(observades)

        # Boles fredes (surten menys del 70% de l'esperat)
        fredes = sorted([n for n in range(1, 50)
                        if freq[n] < freq_esperada * 0.70],
                       key=lambda x: freq[x])

        # Boles calentes (surten més del 130% de l'esperat)
        calentes = sorted([n for n in range(1, 50)
                          if freq[n] > freq_esperada * 1.30],
                         key=lambda x: freq[x], reverse=True)

        resultats_cicles.append({
            'ini': data_ini,
            'fi': data_fi,
            'sorteigs': total_sorteigs,
            'p_valor': p_valor,
            'fredes': fredes,
            'calentes': calentes,
            'freq': freq,
            'freq_esperada': freq_esperada
        })

        dies_cicle = (data_fi - data_ini).days
        print(f"\n📅 Cicle: {data_ini.strftime('%d/%m/%Y')} → {data_fi.strftime('%d/%m/%Y')} ({dies_cicle}d, {total_sorteigs} sorteigs)")
        print(f"   Freq esperada per bola: {freq_esperada:.1f} | Chi-quadrat p = {p_valor:.4f}", end="  →  ")
        if p_valor < 0.05:
            print("✅ Distribució anormal!")
        elif p_valor < 0.10:
            print("⚠️  Distribució lleugerament anormal")
        else:
            print("❌ Distribució normal")

        if fredes:
            print(f"   🔵 FREDES (<70% esperat): {', '.join(f'{n}({freq[n]:.0f})' for n in fredes[:8])}")
        if calentes:
            print(f"   🔴 CALENTES (>130% esperat): {', '.join(f'{n}({freq[n]:.0f})' for n in calentes[:8])}")

    # === ANÀLISI GLOBAL ===
    print(f"\n{'═'*70}")
    print(f"📋 ANÀLISI GLOBAL: LES FREDES COMPENSEN AL CICLE SEGÜENT?")
    print(f"{'═'*70}")

    compensacions = 0
    no_compensacions = 0

    for i in range(len(resultats_cicles) - 1):
        cicle_actual = resultats_cicles[i]
        cicle_seguent = resultats_cicles[i + 1]

        fredes_actuals = set(cicle_actual['fredes'])
        if not fredes_actuals:
            continue

        # Comprova si les fredes del cicle actual surten més al cicle següent
        freq_seg = cicle_seguent['freq']
        freq_esp_seg = cicle_seguent['freq_esperada']

        fredes_que_compensen = [n for n in fredes_actuals
                                if freq_seg[n] > freq_esp_seg]
        fredes_que_no_compensen = [n for n in fredes_actuals
                                   if freq_seg[n] <= freq_esp_seg]

        ratio = len(fredes_que_compensen) / len(fredes_actuals) if fredes_actuals else 0
        compensacions += len(fredes_que_compensen)
        no_compensacions += len(fredes_que_no_compensen)

        print(f"\n   Cicle {cicle_actual['ini'].strftime('%d/%m/%Y')}:")
        print(f"   Fredes: {sorted(fredes_actuals)}")
        print(f"   Compensen al cicle següent: {sorted(fredes_que_compensen)} ({ratio*100:.0f}%)")

    # Resultat final
    total = compensacions + no_compensacions
    if total > 0:
        ratio_global = compensacions / total
        print(f"\n{'═'*70}")
        print(f"📊 RESULTAT FINAL:")
        print(f"   Boles fredes que compensen al cicle següent: {compensacions}/{total} ({ratio_global*100:.1f}%)")
        print(f"\n   ", end="")
        if ratio_global > 0.60:
            print("✅ HIPÒTESI CONFIRMADA: Les fredes tendeixen a compensar!")
            print("      → Té sentit jugar boles fredes del cicle actual")
        elif ratio_global > 0.50:
            print("⚠️  HIPÒTESI FEBLE: Lleuger tendència a compensar")
            print("      → Resultat no concloent")
        else:
            print("❌ HIPÒTESI REBUTJADA: Les fredes NO compensen sistemàticament")
            print("      → No té sentit jugar boles fredes")

    # === PERCENTILS HISTÒRICS ===
    p_valors_historics = [c['p_valor'] for c in resultats_cicles[:-1]]  # exclou cicle actual
    p10 = np.percentile(p_valors_historics, 10)
    p90 = np.percentile(p_valors_historics, 90)

    print(f"\n{'═'*70}")
    print(f"📊 PERCENTILS HISTÒRICS DE P-VALOR:")
    print(f"   Percentil 10 (llindar baix):  {p10:.4f}")
    print(f"   Percentil 90 (llindar alt):   {p90:.4f}")
    print(f"   Rang normal: {p10:.4f} → {p90:.4f}")

    # === CICLE ACTUAL ===
    if resultats_cicles:
        cicle_actual = resultats_cicles[-1]
        print(f"\n{'═'*70}")
        print(f"🎯 CICLE ACTUAL ({cicle_actual['ini'].strftime('%d/%m/%Y')} → avui):")
        print(f"   Sorteigs: {cicle_actual['sorteigs']} | p = {cicle_actual['p_valor']:.4f}")
        if cicle_actual['fredes']:
            print(f"   🔵 Boles FREDES actuals: {', '.join(str(n) for n in cicle_actual['fredes'][:10])}")
            print(f"      → Si la hipòtesi és vàlida, aquestes haurien de sortir aviat")
        if cicle_actual['calentes']:
            print(f"   🔴 Boles CALENTES actuals: {', '.join(str(n) for n in cicle_actual['calentes'][:10])}")
        print(f"{'═'*70}")
    p_actual = cicle_actual['p_valor']
    print(f"   P-valor actual: {p_actual:.4f}", end="  →  ")
    if p_actual < p10:
        print(f"🔴 FORA DEL LÍMIT INFERIOR (p10={p10:.4f}) → Possible biaix real!")
    elif p_actual > p90:
        print(f"🟢 FORA DEL LÍMIT SUPERIOR (p90={p90:.4f}) → Distribució perfectament normal")
    else:
        print(f"🟡 Dins del rang normal ({p10:.4f} → {p90:.4f})")

if __name__ == "__main__":
    sorteigs_primi = carregar_sorteigs(FITXER_PRIMI)
    sorteigs_bono = carregar_sorteigs(FITXER_BONO)

    analitzar_distribucio_cicle(sorteigs_primi, CALIBRATGES_PRIMI, "Primitiva")
    analitzar_distribucio_cicle(sorteigs_bono, CALIBRATGES_BONO, "Bonoloto")