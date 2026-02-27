import csv
import os
from collections import Counter
from datetime import datetime, timedelta
import numpy as np
from scipy.stats import chisquare

FITXER_PRIMI = "Lotoideas.com - Histórico de Resultados - Primitiva - 2013 a 202X(1).csv"
FITXER_BONO = "Lotoideas.com - Histórico de Resultados - Bonoloto - 2013 a 202X(1).csv"

CICLE_PRIMI = 297
CICLE_BONO = 251

# Filtre de cicles: descarta cicles amb massa pocs o massa sorteigs
MIN_SORTEIGS = 50
MAX_SORTEIGS = 500


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
    """Detecta totes les dates de calibratge usant cicle fix"""
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

    # Filtra pics massa propers (menys de cicle/2 dies entre ells)
    pics.sort(key=lambda x: x[0])
    pics_filtrats = []
    for pic in pics:
        if not pics_filtrats or (pic[0] - pics_filtrats[-1][0]).days > cicle // 2:
            pics_filtrats.append(pic)

    return [p[0] for p in pics_filtrats]


def analitzar_distribucio_cicle(sorteigs, calibratges, cicle, nom_loteria):
    """Analitza la distribució de boles dins de cada cicle de calibratge"""
    print(f"\n{'═'*70}")
    print(f"📊 DISTRIBUCIÓ DE BOLES PER CICLE - {nom_loteria.upper()} (cicle {cicle}d)")
    print(f"{'═'*70}")
    print(f"   Calibratges detectats: {len(calibratges)}")
    for c in calibratges:
        print(f"   → {c.strftime('%d/%m/%Y')}")

    # Construeix cicles entre calibratges consecutius
    cicles = []
    for i in range(len(calibratges) - 1):
        cicles.append((calibratges[i], calibratges[i + 1]))
    cicles.append((calibratges[-1], datetime.now()))

    resultats_cicles = []

    for data_ini, data_fi in cicles:
        sorteigs_cicle = [(dt, nums) for dt, nums in sorteigs
                         if dt >= data_ini and dt < data_fi]

        # Filtra cicles massa curts o llargs
        if len(sorteigs_cicle) < MIN_SORTEIGS or len(sorteigs_cicle) > MAX_SORTEIGS:
            dies = (data_fi - data_ini).days
            print(f"\n⏭️  Cicle {data_ini.strftime('%d/%m/%Y')} → {data_fi.strftime('%d/%m/%Y')} "
                  f"({dies}d, {len(sorteigs_cicle)} sorteigs) → DESCARTAT")
            continue

        freq = Counter()
        for _, nums in sorteigs_cicle:
            for n in nums:
                freq[n] += 1

        total_sorteigs = len(sorteigs_cicle)
        freq_esperada = (total_sorteigs * 6) / 49

        observades = [freq[n] for n in range(1, 50)]
        _, p_valor = chisquare(observades)

        fredes = sorted([n for n in range(1, 50)
                        if freq[n] < freq_esperada * 0.70],
                       key=lambda x: freq[x])

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
            print(f"   🔵 FREDES (<70%): {', '.join(f'{n}({freq[n]:.0f})' for n in fredes[:8])}")
        if calentes:
            print(f"   🔴 CALENTES (>130%): {', '.join(f'{n}({freq[n]:.0f})' for n in calentes[:8])}")

    # === ANÀLISI GLOBAL COMPENSACIÓ ===
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

        freq_seg = cicle_seguent['freq']
        freq_esp_seg = cicle_seguent['freq_esperada']

        fredes_que_compensen = [n for n in fredes_actuals if freq_seg[n] > freq_esp_seg]
        ratio = len(fredes_que_compensen) / len(fredes_actuals) if fredes_actuals else 0
        compensacions += len(fredes_que_compensen)
        no_compensacions += len(fredes_actuals) - len(fredes_que_compensen)

        print(f"\n   Cicle {cicle_actual['ini'].strftime('%d/%m/%Y')}:")
        print(f"   Fredes: {sorted(fredes_actuals)}")
        print(f"   Compensen: {sorted(fredes_que_compensen)} ({ratio*100:.0f}%)")

    total = compensacions + no_compensacions
    if total > 0:
        ratio_global = compensacions / total
        print(f"\n{'═'*70}")
        print(f"📊 RESULTAT COMPENSACIÓ:")
        print(f"   Boles fredes que compensen: {compensacions}/{total} ({ratio_global*100:.1f}%)")
        if ratio_global > 0.60:
            print("   ✅ HIPÒTESI CONFIRMADA: Les fredes tendeixen a compensar!")
        elif ratio_global > 0.50:
            print("   ⚠️  HIPÒTESI FEBLE: Lleuger tendència a compensar")
        else:
            print("   ❌ HIPÒTESI REBUTJADA: Les fredes NO compensen sistemàticament")

    # === PERCENTILS HISTÒRICS ===
    p_valors_historics = [c['p_valor'] for c in resultats_cicles[:-1]]
    p10, p90 = None, None
    if p_valors_historics:
        p10 = np.percentile(p_valors_historics, 10)
        p90 = np.percentile(p_valors_historics, 90)
        print(f"\n{'═'*70}")
        print(f"📊 PERCENTILS HISTÒRICS DE P-VALOR:")
        print(f"   Percentil 10: {p10:.4f} | Percentil 90: {p90:.4f}")
        print(f"   Rang normal:  {p10:.4f} → {p90:.4f}")

    # === CICLE ACTUAL ===
    if resultats_cicles:
        cicle_act = resultats_cicles[-1]
        print(f"\n{'═'*70}")
        print(f"🎯 CICLE ACTUAL ({cicle_act['ini'].strftime('%d/%m/%Y')} → avui):")
        print(f"   Sorteigs: {cicle_act['sorteigs']} | p = {cicle_act['p_valor']:.4f}")
        if cicle_act['fredes']:
            print(f"   🔵 FREDES: {', '.join(str(n) for n in cicle_act['fredes'][:10])}")
        if cicle_act['calentes']:
            print(f"   🔴 CALENTES: {', '.join(str(n) for n in cicle_act['calentes'][:10])}")

        p_actual = cicle_act['p_valor']
        print(f"\n   P-valor actual: {p_actual:.4f}", end="  →  ")
        if p10 and p90:
            if p_actual < p10:
                print(f"🔴 FORA DEL LÍMIT INFERIOR (p10={p10:.4f}) → Possible biaix real!")
            elif p_actual > p90:
                print(f"🟢 FORA DEL LÍMIT SUPERIOR (p90={p90:.4f}) → Distribució perfectament normal")
            else:
                print(f"🟡 Dins del rang normal ({p10:.4f} → {p90:.4f})")
        print(f"{'═'*70}")


if __name__ == "__main__":
    print("🔬 ANÀLISI DE DISTRIBUCIÓ PER CICLES DE CALIBRATGE")
    print(f"   CICLE_PRIMI={CICLE_PRIMI}d | CICLE_BONO={CICLE_BONO}d")
    print(f"   Filtre: {MIN_SORTEIGS} ≤ sorteigs ≤ {MAX_SORTEIGS}")

    sorteigs_primi = carregar_sorteigs(FITXER_PRIMI)
    sorteigs_bono = carregar_sorteigs(FITXER_BONO)

    print(f"\n🔍 Detectant calibratges Primitiva...")
    calibratges_primi = detectar_tots_calibratges(sorteigs_primi, CICLE_PRIMI)

    print(f"🔍 Detectant calibratges Bonoloto...")
    calibratges_bono = detectar_tots_calibratges(sorteigs_bono, CICLE_BONO)

    analitzar_distribucio_cicle(sorteigs_primi, calibratges_primi, CICLE_PRIMI, "Primitiva")
    analitzar_distribucio_cicle(sorteigs_bono, calibratges_bono, CICLE_BONO, "Bonoloto")
