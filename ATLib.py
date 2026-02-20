import requests
from bs4 import BeautifulSoup
import csv
import re
import yfinance as yf
import os
import matplotlib
# Forcem backend "headless" abans de qualsevol import de pyplot
os.environ["MPLBACKEND"] = "Agg"
matplotlib.use("Agg")  # backend sense GUI
import matplotlib.pyplot as plt
# Sobreescrivim plt.show perquè no faci res
plt.show = lambda *args, **kwargs: None
import numpy as np
import mplfinance as mpf
import pandas as pd
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import tempfile
from pypnf import PointFigureChart
from collections import Counter
from itertools import combinations


def generar_lotto_recomanacio():
    # --- CONFIGURACIÓ DE DESCÀRREGA ---
    FITXER_PRIMI = "Lotoideas.com - Histórico de Resultados - Primitiva - 2013 a 202X(1).csv"
    FITXER_BONO = "Lotoideas.com - Histórico de Resultados - Bonoloto - 2013 a 202X(1).csv"
    HEADERS = {'User-Agent': 'Mozilla/5.0'}
    
    print("🛰️ Actualitzant dades de loteria des de la web...")
    tasques = [
        ("https://www.lotoideas.com/primitiva-resultados-historicos-de-todos-los-sorteos/", FITXER_PRIMI, "gid=1"),
        ("https://www.lotoideas.com/bonoloto-resultados-historicos-de-todos-los-sorteos/", FITXER_BONO, "gid=0")
    ]
    
    for url, nom, gid in tasques:
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            link = next((a['href'] for a in soup.find_all('a', href=True) if "output=csv" in a['href'] and gid in a['href']), None)
            if link:
                with open(nom, 'wb') as f: 
                    f.write(requests.get(link).content)
                print(f"✅ {nom} actualitzat.")
        except Exception as e:
            print(f"⚠️ Error descarregant {nom}: {e}")

    # --- LÒGICA D'ANÀLISI (90 DIES) ---
    avui = datetime.now()
    lim_mom = avui - timedelta(days=30)
    lim_biaix = avui - timedelta(days=90)

    stats_mom, stats_hist, triplets_cnt = Counter(), Counter(), Counter()
    sort_mom = 0

    for f_nom in [FITXER_PRIMI, FITXER_BONO]:
        if os.path.exists(f_nom):
            with open(f_nom, mode='r', encoding='utf-8') as f:
                reader = csv.reader(f); next(reader)
                for fila in reader:
                    if len(fila) < 7: continue
                    dt = None
                    d_str = fila[0].split(' ')[0].replace('-', '/')
                    for fmt in ["%d/%m/%Y", "%Y/%m/%d"]:
                        try: dt = datetime.strptime(d_str, fmt); break
                        except: continue
                    
                    if not dt: continue
                    nums = sorted([int(n) for n in fila[1:7] if n.strip().isdigit()])
                    
                    if dt >= lim_mom:
                        sort_mom += 1
                        for n in nums: stats_mom[n] += 1
                    if dt >= lim_biaix:
                        for n in nums: stats_hist[n] += 1
                        for t in combinations(nums, 3): triplets_cnt[t] += 1

    scores = []
    top_triplets = [t for t, _ in triplets_cnt.most_common(50)]
    for n in range(1, 50):
        punts = 0
        if stats_mom[n] > (sort_mom * 0.15): punts += 45 
        if stats_hist[n] > 0: punts += (stats_hist[n] * 0.7)
        for t in top_triplets:
            if n in t: punts += 12
        scores.append((n, punts))

    scores.sort(key=lambda x: x[1], reverse=True)
    ap_a = sorted([n for n, p in scores[:6]])
    ap_b = sorted([n for n, p in scores[6:12]])
    
    return (
        f"🎯 *LOTERIA DE DADES* - {avui.strftime('%d/%m/%Y')}\n"
        f"📊 Dades actualitzades ara mateix\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎰 *APOSTA PRINCIPAL*\n"
        f"`{' - '.join(f'{n:02d}' for n in ap_a)}`\n\n"
        f"🎰 *APOSTA SECUNDÀRIA*\n"
        f"`{' - '.join(f'{n:02d}' for n in ap_b)}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 _Cost: 13,00€ / setmana_"
    )

# Funcions per obtenir les receptes d'allstendres
def obtenir_enllacos_des_de_pagina_principal(url_principal):
    resposta = requests.get(url_principal)
    if resposta.status_code == 200:
        soup = BeautifulSoup(resposta.content, 'html.parser')
        enllacos = []
        index_receptes = soup.find('h2', text='Index de Receptes')
        if index_receptes:
            # Trobem tots els enllaços de receptes a partir de l'índex de receptes
            for enllac in index_receptes.find_next('ul').find_all('a', href=True):
                enllacos.append(enllac['href'])
            return enllacos
        else:
            print('No s\'ha trobat cap índex de receptes a la pàgina.')
            return None
    else:
        print('Error en carregar la pàgina principal:', resposta.status_code)
        return None

def obtenir_recepta(enllac_recepta):
    resposta = requests.get(enllac_recepta)
    if resposta.status_code == 200:
        soup = BeautifulSoup(resposta.content, 'html.parser')
        
        # Obtener el nombre de la receta
        nom_recepta_tag = soup.find('h3', class_='post-title')
        nom_recepta = nom_recepta_tag.text.strip() if nom_recepta_tag else "Nom de la recepta no trobat"
        
        # Obtener el contenido de la receta
        contingut_recepta_tag = soup.find('div', class_='post-body')
        contingut_recepta = contingut_recepta_tag.get_text(separator='\n').strip() if contingut_recepta_tag else "Contingut de la recepta no trobat"
        
        # Construir el texto final de la receta
        text_recepta = f"{nom_recepta}\n\n{contingut_recepta}\n\n{enllac_recepta}"
        
        return text_recepta
        
    else:
        return "Error en carregar la recepta."

# Funcions per per mostrar les dades dels esports.
def leer_csv(nombre_archivo):

    datos = []
    with open(nombre_archivo, mode='r', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            datos.append(row)
    return datos

def generar_mensaje(datos):
    meses_numeros = {'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril': 4, 'Mayo': 5, 'Junio': 6, 'Julio': 7, 'Agosto': 8, 'Septiembre': 9, 'Octubre': 10, 'Noviembre': 11, 'Diciembre': 12}
    primeros_meses = sorted(set(row['Mes'] for row in datos))[:3]
    datos_filtrados = [row for row in datos if row['Mes'] in primeros_meses]
    datos_ordenados = sorted(datos_filtrados, key=lambda x: (meses_numeros[x['Mes']], int(re.search(r'\d+', x['Distancia']).group())))

    mensaje = ""
    mes_actual = None
    distancia_anterior = None
    for row in datos_ordenados:
        mes = row['Mes']
        distancia = row['Distancia']
        nombre = row['Nombre']
        dia = row['Día']
        lugar = row['Lugar']

        if mes != mes_actual:
            mensaje += f"\nMes: {mes}\n"
            mes_actual = mes

        if distancia != distancia_anterior:
            mensaje += f"\nDistancia: {distancia}\n"
            distancia_anterior = distancia

        mensaje += f"{dia}-{nombre}-{lugar}\n"

    return mensaje

def obtenir_dades(tickers):
    # Crear un diccionario para almacenar los precios de cierre y la variación
    closing_prices = {}
    var_prices = {}
    result=[]

    # Obtener el precio de cierre y la variación para cada ticker
    for ticker in tickers:
        data = yf.Ticker(ticker).history(period='1wk')  # Obtener los datos del último día
        closing_price = data['Close'].iloc[-1]  # Extraer el precio de cierre
        closing_prices[ticker] = closing_price
        data['Variació_preu_%'] = data['Close'].pct_change() * 100
        var = data['Variació_preu_%'].iloc[-1]
        var_prices[ticker] = var
    
    for ticker in tickers:
        price = closing_prices[ticker]
        var = var_prices[ticker]
        if price < 10:
            result.append(f"{ticker}:  ${round(price, 3)}   {round(var, 2)}%") 
        else:
            result.append(f"{ticker}:  ${round(price)}   {round(var, 2)}%") 
    return "\n".join(result)

def veles(par):
    # Definir el periode de temps respecte avui, en dies
    dies_enrera = 90

    # Calcul de la data d'inci segons el periode de dies estipulat
    inici = (datetime.now() - timedelta(days=dies_enrera)).strftime('%Y-%m-%d')

    # Definir la fecha final como la fecha actual
    final = datetime.now().strftime('%Y-%m-%d')

    # Descarrega les dades del BTC
    btc_data = yf.download(par, period='3mo')

    # print(btc_data.head())

    # Si el DataFrame té MultiIndex a les columnes
    btc_data.columns = btc_data.columns.get_level_values(0)  # agafa només la primera capa

    # Sortida: Open, High, Low, Close, Volume, Price (ja plana)
    # print(btc_data.head())


    darrer_preu_tancament = float(btc_data['Close'].iloc[-1])


    # import mplfinance as mpf

    imagen_path = 'grafica.png'

    hlines = dict(
        hlines=[darrer_preu_tancament],   # només els valors
        linestyle='--',
        colors='b',
        linewidths=1,
        alpha=0.5
    )

    mpf.plot(
        btc_data,
        type='candle',
        hlines=hlines,
        volume=True,
        style='charles',
        title=f'{par} ({round(darrer_preu_tancament)})',
        savefig=imagen_path
    )

    return imagen_path

def pnf(par):
    btc_data = yf.download(par, period='6mo', interval='1d').dropna()

    # Si hi ha MultiIndex a les columnes, aplanem
    if isinstance(btc_data.columns, pd.MultiIndex):
        btc_data.columns = btc_data.columns.droplevel(1)

    darrer_preu_tancament = float(btc_data['Close'].iloc[-1])

    def calcular_tamany_caixa(preu):
        if preu < 0.25: return 0.0625
        elif preu < 1.00: return 0.125
        elif preu < 5.00: return 0.25
        elif preu < 20.00: return 0.50
        elif preu < 100: return 1
        elif preu < 200: return 2
        elif preu < 500: return 4
        elif preu < 1000: return 5
        elif preu < 25000: return 50
        else: return 500

    box = calcular_tamany_caixa(darrer_preu_tancament)
    revers = 3

    imagen_path = 'grafica.png'
    hlines = dict(hlines=[darrer_preu_tancament],
                  colors=['b'],
                  linestyle='--',
                  linewidths=1)

    mpf.plot(
        btc_data,
        type='pnf',
        pnf_params=dict(box_size=box, reversal=revers),
        hlines=hlines,
        volume=True,
        style='charles',
        title=f'P&F {par} - Box/Rev ({box}/{revers}) - Preu({round(darrer_preu_tancament)})',
        ylabel='Preu (USD)',
        savefig=imagen_path,
        # figratio=(6,4),   # amplada:altura
        # figscale=1.5      # es 
    )

    return imagen_path


def transit():
    # Configuració del navegador
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # options.add_argument("--headless") 
    # options.add_argument("--disable-gpu")
    options.add_argument("--start-maximized")
    # options.add_argument("--incognito")  # 🔹 Navegador sense cookies
    options.add_argument(f"--user-data-dir={tempfile.mkdtemp()}")  # 🔹 Perfil temporal
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    try:
        driver.get("https://cit.transit.gencat.cat/cit/AppJava/views/incidents.xhtml")

        # 🔹 Esborrem cookies un cop carregada la web
        driver.delete_all_cookies()

        wait = WebDriverWait(driver, 15)

        # Obrim el desplegable
        dropdown = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "#llistaResultatsForm > div:nth-child(2) > div > div:nth-child(2) > div:nth-child(4) > span > span.selection > span > ul")
        ))
        dropdown.click()

        # Seleccionem l'opció "Barcelona" pel text
        city_option = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//li[contains(text(), 'Barcelona')]")
        ))
        city_option.click()

        # Cliquem el botó de cerca
        search_button = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "#btnCerca")
        ))
        search_button.click()

        # Esperem que aparegui la taula amb afectacions
        afectacions_table = wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "#llista_entitats > div > div.table-responsive table")
        ))

        # Extreiem noms de columna
        header_cells = afectacions_table.find_elements(By.CSS_SELECTOR, "thead tr th")
        column_names = [cell.text.replace("\n", " ").strip() for cell in header_cells]    
        exclude_cols = {"Nivell d'afectació", "Inici"}  # 🔹 Columnes a ignorar
        valid_cols = [col for col in column_names if col not in exclude_cols]


        # Extreiem les files i les convertim en diccionaris
        rows = afectacions_table.find_elements(By.CSS_SELECTOR, "tbody tr")

        missatge = "Afectacions trobades:\n\n"

        for i, row in enumerate(rows, 1):
            
            cells = row.find_elements(By.TAG_NAME, "td")
            row_data = [cell.text.replace("\n", " ").strip() for cell in cells]
            afectacio = dict(zip(column_names, row_data))

            # print(f"Afectació {i}:")
            # for k, v in afectacio.items():
            #     print(f"  {k}: {v}")
            # print("-" * 50)

            missatge += f"➡️ Afectació {i}\n"
            for k, v in afectacio.items():
                missatge += f"{k}: {v}\n"
            missatge += "\n"

        # Enviem tot el missatge a Telegram
        # envia_missatge(missatge)

    finally:
        driver.quit()
        
    return missatge

def diesel():
    urls = [
        "https://preciocombustible.es/barcelona/vilanova-del-valles/14361-esclatoil",
        "https://preciocombustible.es/barcelona/montornes-del-valles/2786-nuroil",
        "https://preciocombustible.es/barcelona/montmelo/12468-ballenoil",
        "https://preciocombustible.es/barcelona/parets-del-valles/14716-bonarea",
        "https://preciocombustible.es/barcelona/cabrera-de-mar/12728-esclatoil",
        "https://preciocombustible.es/barcelona/mataro/14113-gm-oil",
        "https://preciocombustible.es/barcelona/mataro/15825-petroprix",
        "https://preciocombustible.es/barcelona/ripollet/14552-petroprix",
    
    ]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0 Safari/537.36"
    }

    missatge = "Preus Diesel:\n"

    for url in urls:
        
        resposta = requests.get(url, headers=headers)

        soup = BeautifulSoup(resposta.text, "html.parser")

        preu = soup.find("span", itemprop="price")
        gasolinera = soup.select_one("ul li.uk-text-large.uk-text-bold.uk-text-center")
        actualitzacio = soup.select_one(r"body > div > main > div > div > div.uk-grid.uk-child-width-1-2\@m.uk-grid-match.uk-grid-stack > div:nth-child(1) > div > ul > li:nth-child(2)")
        ciutat = soup.select_one("ul li:nth-child(4)")
        preu_float = float(preu.text.replace(",", "."))
        diposit = round(preu_float*35,1)
        dipositEO1 = round((preu_float-0.05)*35,1)
        dipositEO2 = round((preu_float-0.07)*35,1)

        if gasolinera.text == "Esclatoil":
            missatge += f"""
            Gasolinera: {gasolinera.get_text(strip=True) if gasolinera else 'No trobat'}
            Preu: {preu.get_text(strip=True) if preu else 'No trobat'}
            {ciutat.get_text(strip=True) if ciutat else 'No trobat'}
            Dipòsit: {diposit}€
            Dipòsit client: {dipositEO1}€ mati {dipositEO2}€
            """
        else:
            missatge += f"""
            Gasolinera: {gasolinera.get_text(strip=True) if gasolinera else 'No trobat'}
            Preu: {preu.get_text(strip=True) if preu else 'No trobat'}
            {ciutat.get_text(strip=True) if ciutat else 'No trobat'}
            Dipòsit: {diposit}€
            """

    return(missatge)

    
