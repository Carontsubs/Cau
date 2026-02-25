import requests
from bs4 import BeautifulSoup
import csv
import os
from collections import Counter
from itertools import combinations
from datetime import datetime, timedelta
import numpy as np
from scipy.stats import chisquare
from scipy.stats import chi2
from dotenv import load_dotenv

load_dotenv()
TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

FITXER_PRIMI = "Lotoideas.com - Histórico de Resultados - Primitiva - 2013 a 202X(1).csv"
FITXER_BONO = "Lotoideas.com - Histórico de Resultados - Bonoloto - 2013 a 202X(1).csv"
FITXER_NETA = "estadistiques_loteries_NETA.csv"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

# Cicles reals detectats pel detector de calibratges
CICLE_PRIMI = 297
CICLE_BONO = 251
DIES_MOMENTUM_PRIMI = 30
DIES_MOMENTUM_BONO = 25

# Llindars de mode
MODE_POST_CALIBRATGE_DIES = 60
MODE_PRE_CALIBRATGE_DIES = 45


def enviar_telegram(missatge):
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": missatge, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, data=data)
        if r.status_code == 200:
            print("📲 Notificació enviada a Telegram.")
        else:
            print(f"⚠️ Error Telegram: {r.text}")
    except Exception as e:
        print(f"❌ Error: {e}")


def parsejar_data_flexible(data_str):
    data_netejada = data_str.split(' ')[0].replace('-', '/')
    for fmt in ["%d/%m/%Y", "%Y/%m/%d"]:
        try:
            return datetime.strptime(data_netejada, fmt)
        except:
            continue
    return None


def actualitzar_dades():
    print("🛰️  FASE 1: ACTUALITZANT DADES DES DE LA WEB...")
    tasques = [
        ("https://www.lotoideas.com/primitiva-resultados-historicos-de-todos-los-sorteos/", FITXER_PRIMI, "gid=1"),
        ("https://www.lotoideas.com/bonoloto-resultados-historicos-de-todos-los-sorteos/", FITXER_BONO, "gid=0")
    ]
    for url, nom, gid in tasques:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            link = next((a['href'] for a in soup.find_all('a', href=True)
                        if "output=csv" in a['href'] and gid in a['href']), None)
            if link:
                with open(nom, 'wb') as f:
                    f.write(requests.get(link, headers=HEADERS).content)
                print(f"✅ {nom} descarregat i actualitzat.")
        except Exception as e:
            print(f"❌ Error descarregant {nom}. S'usarà la còpia local.")

    dades = []
    for f_nom, tipus in [(FITXER_PRIMI, "Primitiva"), (FITXER_BONO, "Bonoloto")]:
        if os.path.exists(f_nom):
            with open(f_nom, mode='r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)
                for fila in reader:
                    if len(fila) >= 7:
                        nums = [n.strip() for n in fila[1:7] if n.strip().isdigit()]
                        if len(nums) == 6:
                            dades.append({'Data': fila[0], 'Combinacio': f"[{', '.join(nums)}]", 'Origen': tipus})

    with open(FITXER_NETA, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Data', 'Combinacio', 'Origen'])
        writer.writeheader()
        writer.writerows(dades)
    print(f"✅ Base de dades unificada: {len(dades)} sortejos totals.")


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


def detectar_ultim_calibratge(sorteigs, cicle, finestra=90):
    """Detecta l'últim calibratge usant cicle fix"""
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
        return None, None

    mitjana = sum(r[1] for r in resultats) / len(resultats)
    std = np.std([r[1] for r in resultats])
    llindar = mitjana + std

    pics = []
    for data, dif, idx in sorted(resultats, key=lambda x: x[1], reverse=True):
        if dif < llindar:
            break
        if all(abs(idx - p[2]) > 30 for p in pics):
            pics.append((data, dif, idx))
        if len(pics) >= 15:
            break

    pics.sort(key=lambda x: x[0])

    if not pics:
        return None, None

    ultim = pics[-1][0]
    proper = ultim + timedelta(days=cicle)
    return ultim, proper


def determinar_mode(ultim_calibratge, proper_calibratge):
    avui = datetime.now()
    dies_desde_ultim = (avui - ultim_calibratge).days
    dies_fins_proper = (proper_calibratge - avui).days

    if dies_desde_ultim <= MODE_POST_CALIBRATGE_DIES:
        return "POST", dies_desde_ultim, dies_fins_proper
    elif dies_fins_proper <= MODE_PRE_CALIBRATGE_DIES:
        return "PRE", dies_desde_ultim, dies_fins_proper
    else:
        return "MADURESA", dies_desde_ultim, dies_fins_proper


def analitzar_loteria(fitxer, nom_loteria, cicle, dies_momentum, ultim_calibratge, proper_calibratge):
    """Analitza una loteria i retorna les dues apostes recomanades"""
    avui = datetime.now()
    lim_mom = avui - timedelta(days=dies_momentum)
    lim_biaix = ultim_calibratge  # <-- des del darrer calibratge detectat

    mode, dies_desde, dies_fins = determinar_mode(ultim_calibratge, proper_calibratge)

    modes_desc = {
        "POST":     "🟡 POST-CALIBRATGE (dades limitades, baixa confiança)",
        "PRE":      "🔴 PRE-CALIBRATGE (biaix màxim, aprofita ara!)",
        "MADURESA": "🟢 MADURESA (finestra completa, alta fiabilitat)"
    }

    stats_mom = Counter()
    stats_hist = Counter()
    triplets_cnt = Counter()
    sort_mom = 0
    sort_biaix = 0

    if not os.path.exists(fitxer):
        print(f"❌ No s'ha trobat {fitxer}.")
        return None, None

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
                for n in nums: stats_mom[n] += 1
            if dt >= lim_biaix:
                sort_biaix += 1
                for n in nums: stats_hist[n] += 1
                for t in combinations(nums, 3): triplets_cnt[t] += 1

    freq_esperada = (sort_biaix * 6) / 49
    observades = [stats_hist[n] for n in range(1, 50)]
    _, p_valor_global = chisquare(observades)

    significatius = {}
    for n in range(1, 50):
        obs = stats_hist[n]
        chi_n = ((obs - freq_esperada) ** 2) / freq_esperada if freq_esperada > 0 else 0
        p_n = 1 - chi2.cdf(chi_n, df=1)
        significatius[n] = {'p': p_n, 'desviacio': obs - freq_esperada}

    scores = []
    top_triplets = [t for t, _ in triplets_cnt.most_common(50)]

    print(f"\n📊 DESGLOSSAT {nom_loteria.upper()} (Top 12):")
    print("=" * 100)
    print(f"{'BOLA':<8} | {'MOMENTUM':<10} | {'BIAIX':<10} | {'TRIPLETS':<10} | {'CHI p-val':<12} | {'SIGNIFICAT':<12} | {'TOTAL':<10}")
    print("-" * 100)

    for n in range(1, 50):
        punts = 0
        punts_mom = 0
        punts_hist = 0
        punts_trip = 0
        punts_chi = 0

        if stats_mom[n] > (sort_mom * 0.15):
            punts_mom = 40
            punts += 40
        if stats_hist[n] > 0:
            punts_hist = stats_hist[n] * 0.5
            punts += punts_hist
        for t in top_triplets:
            if n in t: punts_trip += 10
        punts += punts_trip

        p_n = significatius[n]['p']
        desv = significatius[n]['desviacio']
        if desv > 0:
            if p_n < 0.05: punts_chi = 50
            elif p_n < 0.10: punts_chi = 25
        else:
            if p_n < 0.05: punts_chi = -50
            elif p_n < 0.10: punts_chi = -25
        punts += punts_chi
        scores.append((n, punts, punts_mom, punts_hist, punts_trip, punts_chi, p_n, desv))

    scores.sort(key=lambda x: x[1], reverse=True)

    for n, total, mom, hist, trip, chi, p_n, desv in scores[:12]:
        signe = "🔺 SOBRE" if desv > 0 else "🔻 SOTA"
        sig = "✅ SÍ" if p_n < 0.10 else "❌ NO"
        print(f"Número {n:02d} | {mom:9.1f} | {hist:9.1f} | {trip:9.1f} | {p_n:11.4f} | {sig:<12} | {total:9.1f}  {signe}")

    print("=" * 100)

    aposta_a = sorted([n for n, _, _, _, _, _, _, _ in scores[:6]])
    aposta_b = sorted([n for n, _, _, _, _, _, _, _ in scores[6:12]])

    print(f"\n{'═'*60}")
    print(f"🎫 {nom_loteria.upper()} - {avui.strftime('%d/%m/%Y')}")
    print(f"   {modes_desc[mode]}")
    print(f"   Finestra biaix: des de {ultim_calibratge.strftime('%d/%m/%Y')} ({dies_desde}d)")
    print(f"   Momentum: {dies_momentum}d | Sorteigs: {sort_biaix} (biaix) / {sort_mom} (momentum)")
    print(f"   Proper calibratge: {proper_calibratge.strftime('%d/%m/%Y')} ({dies_fins}d)")
    print(f"   Chi-quadrat global: p = {p_valor_global:.4f}", end="  →  ")
    if p_valor_global < 0.05:
        print("✅ Biaix SIGNIFICATIU!")
    elif p_valor_global < 0.10:
        print("⚠️  Biaix MARGINAL")
    else:
        print("❌ Sense biaix significatiu")
    print(f"   Números més comuns: {', '.join(str(n) for n, _, _, _, _, _, _, _ in scores[:5])}")
    print(f"🎰 APOSTA PRINCIPAL:  👉 {' - '.join(f'{n:02d}' for n in aposta_a)}")
    print(f"🎰 APOSTA SECUNDÀRIA: 👉 {' - '.join(f'{n:02d}' for n in aposta_b)}")
    print(f"{'═'*60}")

    return aposta_a, aposta_b


def comprovar_apostes():
    if not os.path.exists('apostes_actuals_separades.csv'):
        print("⚠️  No hi ha apostes anteriors guardades.")
        return

    apostes = {}
    data_generacio = ""
    with open('apostes_actuals_separades.csv', mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for fila in reader:
            data_generacio = fila['Data']
            apostes[fila['Tipus']] = [int(n) for n in fila['Combinacio'].split(',')]

    if not apostes:
        print("⚠️  No s'han pogut llegir les apostes.")
        return

    print(f"\n🔍 COMPROVANT APOSTES GENERADES EL {data_generacio} (últims 7 dies)...")
    print("="*60)

    lim = datetime.now() - timedelta(days=7)
    resultats = {k: [] for k in apostes}

    with open(FITXER_NETA, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for fila in reader:
            dt = parsejar_data_flexible(fila['Data'])
            if not dt or dt < lim:
                continue
            nums = set(int(n) for n in fila['Combinacio'].strip('[]').split(','))
            data_fmt = dt.strftime('%d/%m/%Y')
            origen = fila['Origen']
            for tipus, aposta in apostes.items():
                encerts = sorted(nums & set(aposta))
                if len(encerts) >= 3:
                    resultats[tipus].append((data_fmt, origen, encerts, len(encerts)))

    missatge = f"🔍 *COMPROVACIÓ APOSTES* - {data_generacio}\n━━━━━━━━━━━━━━━━━━━━\n"
    etiquetes = {
        'Primi_Principal':  '🔵 PRIMITIVA PRINCIPAL',
        'Primi_Secundaria': '🔵 PRIMITIVA SECUNDÀRIA',
        'Bono_Principal':   '🟡 BONOLOTO PRINCIPAL',
        'Bono_Secundaria':  '🟡 BONOLOTO SECUNDÀRIA'
    }

    for tipus, etiqueta in etiquetes.items():
        if tipus not in apostes:
            continue
        aposta = apostes[tipus]
        print(f"\n🎰 {etiqueta}: {' - '.join(f'{n:02d}' for n in aposta)}")
        print("-"*60)
        missatge += f"\n🎰 *{etiqueta}:* `{' - '.join(f'{n:02d}' for n in aposta)}`\n"
        if resultats[tipus]:
            for data, origen, encerts, n in sorted(resultats[tipus], key=lambda x: x[3], reverse=True):
                encerts_str = ' - '.join(f'{e:02d}' for e in encerts)
                premi = "🏆 PREMI!" if n == 6 else ("⭐⭐⭐" if n == 5 else ("⭐⭐" if n == 4 else "⭐"))
                print(f"  {data} ({origen}): {n} encerts [{encerts_str}] {premi}")
                missatge += f"  {data} ({origen}): {n} encerts {premi}\n"
        else:
            print("  Cap triplet o superior en els últims 7 dies.")
            missatge += "  Cap triplet o superior\n"

    print("\n" + "="*60)
    enviar_telegram(missatge)


def guardar_i_enviar_apostes(avui, primi_a, primi_b, bono_a, bono_b,
                              ultim_primi, proper_primi, ultim_bono, proper_bono):
    with open('apostes_actuals_separades.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Data', 'Tipus', 'Combinacio'])
        writer.writeheader()
        writer.writerow({'Data': avui.strftime('%d/%m/%Y'), 'Tipus': 'Primi_Principal',  'Combinacio': ','.join(str(n) for n in primi_a)})
        writer.writerow({'Data': avui.strftime('%d/%m/%Y'), 'Tipus': 'Primi_Secundaria', 'Combinacio': ','.join(str(n) for n in primi_b)})
        writer.writerow({'Data': avui.strftime('%d/%m/%Y'), 'Tipus': 'Bono_Principal',   'Combinacio': ','.join(str(n) for n in bono_a)})
        writer.writerow({'Data': avui.strftime('%d/%m/%Y'), 'Tipus': 'Bono_Secundaria',  'Combinacio': ','.join(str(n) for n in bono_b)})
    print("\n💾 4 apostes guardades a apostes_actuals_separades.csv")

    tiquet = (
        f"🎫 *NOU TIQUET* - {avui.strftime('%d/%m/%Y')}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔵 *PRIMITIVA*\n"
        f"Principal:  `{' - '.join(f'{n:02d}' for n in primi_a)}`\n"
        f"Secundària: `{' - '.join(f'{n:02d}' for n in primi_b)}`\n"
        f"_Calibratge: {ultim_primi.strftime('%d/%m/%Y')} → proper {proper_primi.strftime('%d/%m/%Y')}_\n\n"
        f"🟡 *BONOLOTO*\n"
        f"Principal:  `{' - '.join(f'{n:02d}' for n in bono_a)}`\n"
        f"Secundària: `{' - '.join(f'{n:02d}' for n in bono_b)}`\n"
        f"_Calibratge: {ultim_bono.strftime('%d/%m/%Y')} → proper {proper_bono.strftime('%d/%m/%Y')}_\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    enviar_telegram(tiquet)


if __name__ == "__main__":
    actualitzar_dades()
    comprovar_apostes()

    avui = datetime.now()

    # Detecta calibratges per separat
    sorteigs_primi = carregar_sorteigs(FITXER_PRIMI)
    sorteigs_bono = carregar_sorteigs(FITXER_BONO)

    ultim_primi, proper_primi = detectar_ultim_calibratge(sorteigs_primi, CICLE_PRIMI)
    ultim_bono, proper_bono = detectar_ultim_calibratge(sorteigs_bono, CICLE_BONO)

    print(f"\n📅 CALIBRATGES DETECTATS:")
    print(f"   🔵 Primitiva: últim {ultim_primi.strftime('%d/%m/%Y')} → proper {proper_primi.strftime('%d/%m/%Y')} ({(proper_primi - avui).days}d)")
    print(f"   🟡 Bonoloto:  últim {ultim_bono.strftime('%d/%m/%Y')} → proper {proper_bono.strftime('%d/%m/%Y')} ({(proper_bono - avui).days}d)")

    # Analitza cada loteria des del seu darrer calibratge
    primi_a, primi_b = analitzar_loteria(FITXER_PRIMI, "Primitiva", CICLE_PRIMI, DIES_MOMENTUM_PRIMI, ultim_primi, proper_primi)
    bono_a,  bono_b  = analitzar_loteria(FITXER_BONO,  "Bonoloto",  CICLE_BONO,  DIES_MOMENTUM_BONO,  ultim_bono,  proper_bono)

    if primi_a and bono_a:
        guardar_i_enviar_apostes(avui, primi_a, primi_b, bono_a, bono_b,
                                  ultim_primi, proper_primi, ultim_bono, proper_bono)