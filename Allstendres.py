from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, Application, ContextTypes
import ATLib as at
import os
from dotenv import load_dotenv

load_dotenv() 

TOKEN = os.getenv("TOKEN_TELEGRAM")

# Función del comandos
async def lotto(update, context: ContextTypes.DEFAULT_TYPE):
    # Opcional: Pots posar un missatge de "processant" si triga molt
    # await update.message.reply_text("🔎 Analitzant biaixos dels últims 90 dies...")
    
    message = at.generar_lotto_recomanacio()
    # Enviem amb parse_mode=Markdown per veure les negretes i el text tipus codi
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=message, 
        parse_mode='Markdown'
    )


async def veles(update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Per veure les grafiques en veles disponibles, /Veles_BTC, /Veles_BNB, /Veles_ETH")

async def pnf(update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Per veure les grafiques Punt i Figura disponibles,/PnF_BTC, /PnF_BNB, /PnF_ETH ")

async def veles_btc(update, context: ContextTypes.DEFAULT_TYPE):
    imagen_path = at.veles('BTC-USD')
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(imagen_path, 'rb'))

async def pnf_btc(update, context: ContextTypes.DEFAULT_TYPE):
    imagen_path = at.pnf('BTC-USD')
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(imagen_path, 'rb'))

async def veles_bnb(update, context: ContextTypes.DEFAULT_TYPE):
    imagen_path = at.veles('BNB-USD')
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(imagen_path, 'rb'))

async def pnf_bnb(update, context: ContextTypes.DEFAULT_TYPE):
    imagen_path = at.pnf('BNB-USD')
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(imagen_path, 'rb'))

async def veles_eth(update, context: ContextTypes.DEFAULT_TYPE):
    imagen_path = at.veles('ETH-USD')
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(imagen_path, 'rb'))

async def pnf_eth(update, context: ContextTypes.DEFAULT_TYPE):
    imagen_path = at.pnf('ETH-USD')
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(imagen_path, 'rb'))

async def preus(update, context: ContextTypes.DEFAULT_TYPE):
    tickers = ['BTC-USD', 'BNB-USD', 'ETH-USD', "DOGE-USD","SOL-USD"]
    message = at.obtenir_dades(tickers)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)

async def diesel(update, context: ContextTypes.DEFAULT_TYPE):
    message = at.diesel()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)

async def transit(update, context: ContextTypes.DEFAULT_TYPE):
    message = at.transit()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)

async def receptes(update, context: ContextTypes.DEFAULT_TYPE) -> None:
    enllacos = at.obtenir_enllacos_des_de_pagina_principal('https://allstendres.blogspot.com')
    if enllacos:
        message = "Receptes disponibles:\n\n"
        for idx, enllac_recepta in enumerate(enllacos, 1):
            nom_recepta = enllac_recepta.split('/')[-1].replace('-', ' ').title()[:-5]
            message += f"{idx}. {nom_recepta}\n"
        message += "\nSelecciona una recepte utilizant /selecciona X [X = número de la recepta]."
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("No s'han pogut obtenir les receptes disponibles.")

async def selecciona(update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) == 0:
        await update.message.reply_text(
            "Usa: /selecciona X [X = número de la recepta] per seleccionar una recepta."
        )
    else:
        num_recepta = int(args[0])
        enllacos = at.obtenir_enllacos_des_de_pagina_principal('https://allstendres.blogspot.com')
        if 1 <= num_recepta <= len(enllacos):
            enllac_recepta = enllacos[num_recepta - 1]
            recepta = at.obtenir_recepta(enllac_recepta)
            if recepta:
                await update.message.reply_text(recepta)
        else:
            await update.message.reply_text("Selecció no vàlida.")

async def start(update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hola! Per veure les receptes disponibles, usa /receptes.\nUsa /lotto per veure la combinacio suggerida dde la setmana\n /transit per veure afectacions a BCN\n I /diesel per veure els preus de Diesel")

# Execucio del bot.        
if __name__ == '__main__':
    # Token del bot proporcionado por BotFather
    # updater = Updater(TOKEN)
    application = Application.builder().token(TOKEN).build()
    
    # dispatcher = updater.dispatcher

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("Transit", transit))
    application.add_handler(CommandHandler("receptes", receptes))
    application.add_handler(CommandHandler("selecciona", selecciona))
    application.add_handler(CommandHandler("Preus", preus))
    application.add_handler(CommandHandler("veles", veles))
    application.add_handler(CommandHandler("diesel", diesel))
    application.add_handler(CommandHandler("PnF", pnf))
    application.add_handler(CommandHandler("Veles_BTC", veles_btc))
    application.add_handler(CommandHandler("PnF_BTC", pnf_btc))
    application.add_handler(CommandHandler("Veles_BNB", veles_bnb))
    application.add_handler(CommandHandler("PnF_BNB", pnf_bnb))
    application.add_handler(CommandHandler("Veles_ETH", veles_eth))
    application.add_handler(CommandHandler("PnF_ETH", pnf_eth))
    application.add_handler(CommandHandler("lotto", lotto))

    # Start del bot
    application.run_polling()

    # Detener el bot con Ctrl + C
    # updater.idle()