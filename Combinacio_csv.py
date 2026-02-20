import csv
import os

def fusionar_historials():
    fitxer_primi = "Lotoideas.com - Histórico de Resultados - Primitiva - 2013 a 202X(1).csv"
    fitxer_bono = "Lotoideas.com - Histórico de Resultados - Bonoloto - 2013 a 202X(1).csv"
    fitxer_sortida = "estadistiques_loteries_NETA.csv"

    dades_totals = []
    configuracio = [(fitxer_primi, "Primitiva"), (fitxer_bono, "Bonoloto")]

    for nom_fitxer, tipus in configuracio:
        if os.path.exists(nom_fitxer):
            print(f"📂 Analitzant línies de: {nom_fitxer}")
            with open(nom_fitxer, mode='r', encoding='utf-8') as f:
                # Llegim com a llista simple, no com a diccionari, per evitar errors de columnes buides
                reader = csv.reader(f)
                capçalera = next(reader) # Saltem la primera fila
                
                for fila in reader:
                    if len(fila) < 7: continue # Saltem línies buides o incompletes
                    
                    try:
                        data = fila[0] # La data sol ser la primera
                        # Agafem els 6 números (solen ser de la posició 1 a la 6)
                        # Netegem cada valor per si hi ha espais
                        numeros = [n.strip() for n in fila[1:7] if n.strip().isdigit()]
                        
                        if len(numeros) == 6:
                            combinacio_neta = "[" + ", ".join(numeros) + "]"
                            dades_totals.append({
                                'Data': data,
                                'Combinacio': combinacio_neta,
                                'Origen': tipus
                            })
                    except:
                        continue
        else:
            print(f"⚠️ No trobat: {nom_fitxer}")

    if not dades_totals:
        print("❌ Error: No s'ha pogut extreure cap combinació. Revisa que el fitxer no estigui obert en Excel.")
        return

    # Escriure el fitxer final
    try:
        with open(fitxer_sortida, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['Data', 'Combinacio', 'Origen'])
            writer.writeheader()
            writer.writerows(dades_totals)
        
        print("\n" + "═"*50)
        print(f"✅ FUSIÓ COMPLETADA")
        print(f"📊 Total sortejos: {len(dades_totals)}")
        print(f"📝 Exemple: {dades_totals[0]['Combinacio']}")
        print("═"*50)
    except Exception as e:
        print(f"❌ Error escrivint el fitxer: {e}")

if __name__ == "__main__":
    fusionar_historials()