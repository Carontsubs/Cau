import re
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
from dotenv import load_dotenv #Importem la funció per carregar .env

# 🔑 AFEGEIX les teves dades
load_dotenv()
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def enviar_telegram(missatge):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": missatge}
    requests.post(url, data=data)

options = Options()
options.add_argument("--headless")  # opcional, perquè no s'obri Chrome
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    driver.get("https://nauticmasnou.com/meteo/")

    # Acceptar cookies si cal
    try:
        boto_cookies = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#wt-cli-accept-all-btn"))
        )
        boto_cookies.click()
    except:
        pass

    # Entrar a l'iframe [1] (Weatherlink)
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    driver.switch_to.frame(iframes[1])

    # Temperatura actual
    temperatura_elem = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.col-8.no-padding"))
    )
    temperatura_valor = float(re.sub(r"[^\d,]", "", temperatura_elem.text.strip()).replace(",", "."))

    # Màx i mín
    hi_lo_elem = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.temp-hi-lo"))
    )
    spans = hi_lo_elem.find_elements(By.TAG_NAME, "span")

    high_valor = float(re.sub(r"[^\d,]", "", spans[0].text.strip()).replace(",", "."))
    high_time = spans[1].text.strip()

    low_valor = float(re.sub(r"[^\d,]", "", spans[2].text.strip()).replace(",", "."))
    low_time = spans[3].text.strip()

    # Missatge formatat
    missatge = (
        f"Meteo Masnou\n"
        f"Actual: {temperatura_valor} °C\n"
        f"Màx: {high_valor} °C {high_time}\n"
        f"Mín: {low_valor} °C {low_time}"
    )

    # Enviar per Telegram
    enviar_telegram(missatge)
    # print("✅ Missatge enviat per Telegram!")

finally:
    driver.quit()
