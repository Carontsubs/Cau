import csv
import os
from collections import Counter
from itertools import combinations
from datetime import datetime, timedelta

def detectar_patrons_fisics():
    fitxer = "estadistiques_loteries_NETA.csv"
    
    if not os.path.exists(fitxer):
        print("Error: No es troba el fitxer d'estadístiques.")
        return

    # --- MENÚ DE SELECCIÓ DE PERÍODE ---
    print("\n" + "═"*40)
    print("   CONFIGURACIÓ DE L'ANÀLISI")
    print("═"*40)
    print("1. Tota l'estadística")
    print("2. Últims 2 anys")
    print("3. Últim any")
    print("4. Últims 6 mesos")
    print("5. Introduir data manual (DD/MM/YYYY)")
    print("6. Introduir número de DIES enrere")
    
    opcio = input("\nTria una opció (1-6): ")

    avui = datetime.now()
    data_limit = None

    if opcio == '2':
        data_limit = avui - timedelta(days=2*365)
    elif opcio == '3':
        data_limit = avui - timedelta(days=365)
    elif opcio == '4':
        data_limit = avui - timedelta(days=182)
    elif opcio == '5':
        data_str = input("Introdueix la data d'inici (Ex: 01/01/2024): ")
        try:
            data_limit = datetime.strptime(data_str, "%d/%m/%Y")
        except ValueError:
            print("Format de data incorrecte. S'analitzarà tota l'estadística.")
    elif opcio == '6':
        try:
            n_dies = int(input("Quants dies enrere vols analitzar? "))
            data_limit = avui - timedelta(days=n_dies)
        except ValueError:
            print("Número de dies no vàlid. S'analitzarà tota l'estadística.")

    comptador_triplets = Counter()
    total_sortejos = 0

    try:
        with open(fitxer, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for fila in reader:
                try:
                    # Neteja i format de data flexible
                    data_raw = fila['Data'].split(' ')[0].replace('-', '/')
                    data_sorteig = datetime.strptime(data_raw, "%d/%m/%Y")
                    
                    if data_limit and data_sorteig < data_limit:
                        continue

                    neteja = fila['Combinacio'].replace('[', '').replace(']', '').replace(' ', '')
                    numeros = sorted([int(n) for n in neteja.split(',')])
                    
                    # Generem totes les combinacions de 3 (triplets)
                    for triplet in combinations(numeros, 3):
                        comptador_triplets[triplet] += 1
                    total_sortejos += 1
                except:
                    continue

        if total_sortejos == 0:
            print("❌ No s'han trobat sortejos en aquest període.")
            return

        # Probabilitat teòrica d'un triplet: 20/18424 = 0.00108548
        prob_teorica = (20 / 18424) 

        ranking = sorted(comptador_triplets.items(), key=lambda x: x[1], reverse=True)

        print("\n" + "█"*95)
        print(f"   ANÀLISI DE BIAIX I MULTIPLICADOR TEÒRIC")
        desc_periode = f"Des de {data_limit.strftime('%d/%m/%Y')}" if data_limit else "Tota la sèrie"
        print(f"   Període: {desc_periode} | Sortejos analitzats: {total_sortejos}")
        print("█"*95)
        print(f"{'TRIPLET (Números)':<20} | {'COPS':<6} | {'% FREQ':<10} | {'ESP. TEÒRICA':<12} | {'MULTIPLICADOR'}")
        print("-" * 95)

        # Mostrem el Top 25
        for triplet, cops in ranking[:25]:
            freq_real = (cops / total_sortejos)
            esperats_teorics = total_sortejos * prob_teorica
            multiplicador = freq_real / prob_teorica
            
            # Icona de foc si el multiplicador és > 2.0 (el doble de la probabilitat)
            foc = "🔥" if multiplicador >= 2.0 else "  "
            
            print(f"{str(list(triplet)):<20} | {cops:<6} | {freq_real*100:6.2f}%   | {esperats_teorics:8.2f}     | {multiplicador:6.2f}x {foc}")

        print("█"*95)
        print(f"💡 El Multiplicador indica quantes vegades més surt el triplet respecte a l'atzar pur.")
        print("█"*95 + "\n")

    except Exception as e:
        print(f"Error en l'anàlisi: {e}")

if __name__ == "__main__":
    detectar_patrons_fisics()