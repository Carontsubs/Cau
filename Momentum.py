import csv
import os
from collections import Counter
from datetime import datetime, timedelta

def parsejar_data_flexible(data_str):
    data_netejada = data_str.split(' ')[0].replace('-', '/')
    formats = ["%d/%m/%Y", "%Y/%m/%d"]
    for fmt in formats:
        try:
            return datetime.strptime(data_netejada, fmt)
        except ValueError:
            continue
    return None

def analitzar_creixement():
    fitxer = "estadistiques_loteries_NETA.csv"
    if not os.path.exists(fitxer): return

    avui = datetime.now()
    # Finestra A: El Present (últims 30 dies)
    limit_present = avui - timedelta(days=30)
    # Finestra B: El Passat de control (dels 30 als 180 dies enrere)
    limit_passat = avui - timedelta(days=180)

    stats_present = Counter()
    stats_passat = Counter()
    sortejos_present = 0
    sortejos_passat = 0

    try:
        with open(fitxer, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for fila in reader:
                data_s = parsejar_data_flexible(fila['Data'])
                if not data_s: continue

                neteja = fila['Combinacio'].replace('[', '').replace(']', '').replace(' ', '')
                nums = [int(n) for n in neteja.split(',')]

                if data_s >= limit_present:
                    sortejos_present += 1
                    for n in nums: stats_present[n] += 1
                elif limit_present > data_s >= limit_passat:
                    sortejos_passat += 1
                    for n in nums: stats_passat[n] += 1

        if sortejos_present == 0 or sortejos_passat == 0:
            print("Falten dades per comparar períodes.")
            return

        # Calculem el creixement
        creixement = []
        for n in range(1, 50):
            freq_pres = (stats_present[n] / sortejos_present) * 100
            freq_pass = (stats_passat[n] / sortejos_passat) * 100
            diferencia = freq_pres - freq_pass
            creixement.append((n, freq_pass, freq_pres, diferencia))

        # Ordenem per major creixement
        creixement.sort(key=lambda x: x[3], reverse=True)

        print("\n" + "🚀"*20)
        print("🔍 DETECTOR D'EXPLOSIÓ (MOMENTUM)")
        print(f"Present: {sortejos_present} sort. | Passat: {sortejos_passat} sort.")
        print("🚀"*20)
        print(f"{'BOLA':<6} | {'FREQ ABANS':<12} | {'FREQ ARA':<12} | {'CREIXEMENT'}")
        print("-" * 55)

        for n, f_vella, f_nova, diff in creixement[:10]:
            print(f"{n:02d}     | {f_vella:6.1f}%      | {f_nova:6.1f}%      | +{diff:5.1f}% 🔥")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analitzar_creixement()