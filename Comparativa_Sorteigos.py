import csv
import os
from collections import Counter
from itertools import combinations
from datetime import datetime, timedelta
from scipy.stats import chisquare
from scipy.stats import chi2

FITXER_PRIMI = "Lotoideas.com - Histórico de Resultados - Primitiva - 2013 a 202X(1).csv"
FITXER_BONO = "Lotoideas.com - Histórico de Resultados - Bonoloto - 2013 a 202X(1).csv"

# Intervals reals detectats pel detector de calibratges
DIES_BIAIX_PRIMI = 297
DIES_BIAIX_BONO = 251
DIES_MOMENTUM_PRIMI = 30
DIES_MOMENTUM_BONO = 25

def parsejar_data_flexible(data_str):
    data_netejada = data_str.split(' ')[0].replace('-', '/')
    for fmt in ["%d/%m/%Y", "%Y/%m/%d"]:
        try:
            return datetime.strptime(data_netejada, fmt)
        except:
            continue
    return None

def analitzar_loteria(fitxer, nom_loteria, dies_biaix, dies_momentum):
    avui = datetime.now()
    lim_mom = avui - timedelta(days=dies_momentum)
    lim_biaix = avui - timedelta(days=dies_biaix)

    stats_mom = Counter()
    stats_hist = Counter()
    triplets_cnt = Counter()
    sort_mom = 0
    sort_biaix = 0

    if not os.path.exists(fitxer):
        print(f"❌ No s'ha trobat {fitxer}.")
        return

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
            nums = sorted([int(n) for n in nums_raw])
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

    # Test chi-quadrat
    freq_esperada = (sort_biaix * 6) / 49
    observades = [stats_hist[n] for n in range(1, 50)]
    _, p_valor_global = chisquare(observades)

    significatius = {}
    for n in range(1, 50):
        obs = stats_hist[n]
        chi_n = ((obs - freq_esperada) ** 2) / freq_esperada if freq_esperada > 0 else 0
        p_n = 1 - chi2.cdf(chi_n, df=1)
        significatius[n] = {'p': p_n, 'desviacio': obs - freq_esperada}

    # Càlcul de scores
    scores = []
    top_triplets = [t for t, _ in triplets_cnt.most_common(50)]

    for n in range(1, 50):
        punts = 0
        if stats_mom[n] > (sort_mom * 0.15):
            punts += 40
        if stats_hist[n] > 0:
            punts += stats_hist[n] * 0.5
        for t in top_triplets:
            if n in t:
                punts += 10
        p_n = significatius[n]['p']
        desv = significatius[n]['desviacio']
        if desv > 0:
            if p_n < 0.05:
                punts += 50
            elif p_n < 0.10:
                punts += 25
        else:
            if p_n < 0.05:
                punts -= 50
            elif p_n < 0.10:
                punts -= 25
        scores.append((n, punts))

    scores.sort(key=lambda x: x[1], reverse=True)
    aposta_a = sorted([n for n, _ in scores[:6]])
    aposta_b = sorted([n for n, _ in scores[6:12]])

    print(f"\n{'═'*55}")
    print(f"🎫 {nom_loteria.upper()} - {avui.strftime('%d/%m/%Y')}")
    print(f"{'═'*55}")
    print(f"   Finestra biaix: {dies_biaix} dies (interval calibratge real)")
    print(f"   Sorteigs analitzats ({dies_momentum}): {sort_mom}")
    print(f"   Sorteigs analitzats ({dies_biaix}d biaix): {sort_biaix}")
    print(f"   Chi-quadrat global: p = {p_valor_global:.4f}", end="  →  ")
    if p_valor_global < 0.05:
        print("✅ Biaix significatiu!")
    elif p_valor_global < 0.10:
        print("⚠️  Biaix marginal")
    else:
        print("❌ Sense biaix")
    print(f"   Números més comuns: {', '.join(str(n) for n, _ in stats_hist.most_common(5))}")
    print(f"🎰 APOSTA PRINCIPAL:  {' - '.join(f'{n:02d}' for n in aposta_a)}")
    print(f"🎰 APOSTA SECUNDÀRIA: {' - '.join(f'{n:02d}' for n in aposta_b)}")
    print(f"{'═'*55}")

if __name__ == "__main__":
    analitzar_loteria(FITXER_PRIMI, "Primitiva", DIES_BIAIX_PRIMI, DIES_MOMENTUM_PRIMI)
    analitzar_loteria(FITXER_BONO,  "Bonoloto",  DIES_BIAIX_BONO,  DIES_MOMENTUM_BONO)