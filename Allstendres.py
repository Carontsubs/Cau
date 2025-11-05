from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import ATLib as at
import os
from dotenv import load_dotenv #Importem la funció per carregar .env

load_dotenv() 
TOKEN = os.getenv("BOT_TOKEN")

# 🌐 NOVES VARIABLES NECESSÀRIES PER A RENDER
# 1. El PORT on ha d'escoltar el servidor (Render l'estableix automàticament)
PORT = int(os.environ.get('PORT', 8080))

# 2. L'URL del teu servei Render (la necessitem per configurar el Webhook a Telegram)
# Aquesta variable l'hauràs de crear a l'entorn de Render amb el domini del teu servei.
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')

# Función del comandos
def veles(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Per veure les grafiques en veles disponibles, /Veles_BTC, /Veles_BNB, /Veles_ETH")

def pnf(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Per veure les grafiques Punt i Figura disponibles,/PnF_BTC, /PnF_BNB, /PnF_ETH ")

def veles_btc(update,context):
    imagen_path = at.veles('BTC-USD')
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(imagen_path, 'rb'))

def pnf_btc(update,context):
    imagen_path = at.pnf('BTC-USD')
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(imagen_path, 'rb'))

def veles_bnb(update,context):
    imagen_path = at.veles('BNB-USD')
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(imagen_path, 'rb'))

def pnf_bnb(update,context):
    imagen_path = at.pnf('BNB-USD')
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(imagen_path, 'rb'))

def veles_eth(update,context):
    imagen_path = at.veles('ETH-USD')
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(imagen_path, 'rb'))

def pnf_eth(update,context):
    imagen_path = at.pnf('ETH-USD')
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(imagen_path, 'rb'))

def preus(update, context):
    tickers = ['BTC-USD', 'BNB-USD', 'ETH-USD', 'DOGE-USD', 'SOL-USD']
    message = at.obtenir_dades(tickers)
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)

def temperatura(update, context):
    message = at.temperatura()
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)

def diesel(update, context):
    message = at.diesel()
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)

def transit(update, context):
    message = at.transit()
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)

def receptes(update: Update, context: CallbackContext) -> None:
    enllacos = at.obtenir_enllacos_des_de_pagina_principal('https://allstendres.blogspot.com')
    if enllacos:
        message = "Receptes disponibles:\n\n"
        for idx, enllac_recepta in enumerate(enllacos, 1):
            nom_recepta = enllac_recepta.split('/')[-1].replace('-', ' ').title()[:-5]
            message += f"{idx}. {nom_recepta}\n"
        message += "\nSelecciona una recepte utilizant /selecciona X [X = número de la recepta]."
        update.message.reply_text(message)
    else:
        update.message.reply_text("No s'han pogut obtenir les receptes disponibles.")

def selecciona(update: Update, context: CallbackContext) -> None:
    args = context.args
    if len(args) == 0:
        update.message.reply_text(
            "Usa: /selecciona X [X = número de la recepta] per seleccionar una recepta."
        )
    else:
        num_recepta = int(args[0])
        enllacos = at.obtenir_enllacos_des_de_pagina_principal('https://allstendres.blogspot.com')
        if 1 <= num_recepta <= len(enllacos):
            enllac_recepta = enllacos[num_recepta - 1]
            recepta = at.obtenir_recepta(enllac_recepta)
            if recepta:
                update.message.reply_text(recepta)
        else:
            update.message.reply_text("Selecció no vàlida.")

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Hola! Per veure les receptes disponibles, usa /receptes.\nUsa /preus, /veles i /PnF per veure les dades de cryptos\n /transit per veure afectacions a BCN\n I /diesel per veure els preus de Diesel\n I /temperatura per la Temperatura d'avui de Masnou")

# Execucio del bot.        
if __name__ == '__main__':
    # Token del bot proporcionado por BotFather
    updater = Updater(TOKEN)
    
    dispatcher = updater.dispatcher

    # Handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("Temperatura", temperatura))
    dispatcher.add_handler(CommandHandler("Transit", transit))
    dispatcher.add_handler(CommandHandler("receptes", receptes))
    dispatcher.add_handler(CommandHandler("selecciona", selecciona))
    dispatcher.add_handler(CommandHandler("Preus", preus))
    dispatcher.add_handler(CommandHandler("veles", veles))
    dispatcher.add_handler(CommandHandler("diesel", diesel))
    dispatcher.add_handler(CommandHandler("PnF", pnf))
    dispatcher.add_handler(CommandHandler("Veles_BTC", veles_btc))
    dispatcher.add_handler(CommandHandler("PnF_BTC", pnf_btc))
    dispatcher.add_handler(CommandHandler("Veles_BNB", veles_bnb))
    dispatcher.add_handler(CommandHandler("PnF_BNB", pnf_bnb))
    dispatcher.add_handler(CommandHandler("Veles_ETH", veles_eth))
    dispatcher.add_handler(CommandHandler("PnF_ETH", pnf_eth))

# CANVI CLAU PER A DESPLEGAMENT EN SERVIDOR WEB (Render)

    if WEBHOOK_URL:
        # 1. Configurar Webhook
        updater.start_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,  # Utilitzem el token com a path secret
            webhook_url=WEBHOOK_URL + TOKEN
        )
        
        # 2. Assegurar-nos que Telegram utilitzi aquesta URL
        print(f"Iniciant bot en mode Webhook a: {WEBHOOK_URL}")
        
    else:
        # Mode per defecte: Long Polling (bo per a proves locals si falla WEBHOOK_URL)
        print("Mode Long Polling (local). Per utilitzar Webhooks, defineix WEBHOOK_URL.")
        updater.start_polling()
    
    # Mantenir el procés viu fins que el servidor l'aturi
    updater.idle()