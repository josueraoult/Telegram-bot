import os
import time
import json
import requests
from typing import Dict, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# Config
BOT_TOKEN = "7059448299:AAGTyg3EIlnQNe91LH49yWojUjHLj9HPqx4"
GEMINI_API_KEY = "AIzaSyAArErZGDDJx7DJwExgY_pPWmN7Tjai8nk"
ADMIN_FILE = "admins.json"
REQUEST_FILE = "requests.json"
PRIMARY_ADMIN = 6100575282

WELCOME_MSG = """🌟 Commandes disponibles :
/help - Affiche ce message
/uptime - Voir le temps de fonctionnement
/uid - Afficher votre ID Telegram
/request [raison] - Demander les droits admin
/adminlist - Liste des admins (admin seulement)
"""

MENU_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("GPT4o", callback_data="gpt4o")],
    [InlineKeyboardButton("Ghibli Studio", callback_data="ghibli")],
    [InlineKeyboardButton("YouTube Download", callback_data="youtube")],
    [InlineKeyboardButton("Aide", callback_data="help")]
])

ADMINS = []
REQUESTS = {}
bot_start_time = time.time()
USER_STATES = {}

def load_data(filename: str, default=None):
    if not os.path.exists(filename):
        with open(filename, 'w') as f:
            json.dump(default if default is not None else [], f)
    with open(filename, 'r') as f:
        return json.load(f)

def save_data(data, filename: str):
    with open(filename, 'w') as f:
        json.dump(data, f)

ADMINS = load_data(ADMIN_FILE, [PRIMARY_ADMIN])
REQUESTS = load_data(REQUEST_FILE, {})

# Fonction pour interroger l'API Gemini
def get_gemini_response(user_input: str) -> str:
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [
                {
                    "parts": [{"text": user_input}]
                }
            ]
        }
        headers = {"Content-Type": "application/json"}

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print("❌ Erreur Gemini API:", e)
        return "⚠️ Erreur lors de la connexion à l'IA."

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type == "private":
        await update.message.reply_text("Bienvenue ! Choisis une option :", reply_markup=MENU_KEYBOARD)

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "gpt4o":
        USER_STATES[user_id] = "gpt"
        await query.message.reply_text("Pose ta question à GPT4o.")
    elif query.data == "ghibli":
        USER_STATES[user_id] = "ghibli"
        await query.message.reply_text("Envoie une image pour la transformer en style Ghibli.")
    elif query.data == "youtube":
        await query.message.reply_text("Fonctionnalité en maintenance.\n👨‍🔧👩‍💻", reply_markup=MENU_KEYBOARD)
    elif query.data == "help":
        await help_cmd(update, context)

# GPT4o traitement texte
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if USER_STATES.get(user_id) == "gpt":
        ask = update.message.text
        result = get_gemini_response(ask)
        await update.message.reply_text(result)
        USER_STATES[user_id] = None

# Ghibli traitement image
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if USER_STATES.get(user_id) == "ghibli":
        photo_file = await update.message.photo[-1].get_file()
        photo_path = f"{user_id}_image.jpg"
        await photo_file.download_to_drive(photo_path)

        with open(photo_path, "rb") as f:
            files = {'fileToUpload': f}
            data = {'reqtype': 'fileupload'}
            r = requests.post("https://catbox.moe/user/api.php", data=data, files=files)
            image_url = r.text.strip()

        ghibli_api_url = f"https://jonell01-ccprojectsapihshs.hf.space/api/ghibli?url={image_url}&type=direct"
        response = requests.get(ghibli_api_url)

        if response.status_code == 200:
            ghibli_path = f"{user_id}_ghibli.jpg"
            with open(ghibli_path, "wb") as out:
                out.write(response.content)
            await update.message.reply_photo(photo=open(ghibli_path, "rb"))
        else:
            await update.message.reply_text("Erreur lors de la génération d'image.")

        USER_STATES[user_id] = None

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = WELCOME_MSG
    if user_id in ADMINS:
        text += "\n🔧 Commandes Admin : /approve /reject /requests /notify /admin"
    await update.effective_chat.send_message(text, reply_markup=MENU_KEYBOARD)

async def uptime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uptime_sec = int(time.time() - bot_start_time)
    h, m, s = uptime_sec // 3600, (uptime_sec % 3600) // 60, uptime_sec % 60
    await update.message.reply_text(f"⏱ Uptime: {h}h {m}m {s}s")

async def get_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    await update.message.reply_text(
        f"👤 Nom : {user.full_name}\n🆔 ID : <code>{user.id}</code>\n📛 Username : @{user.username or 'N/A'}",
        parse_mode='HTML'
    )

# Lancement du bot
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("uptime", uptime))
    app.add_handler(CommandHandler("uid", get_user_id))
    app.add_handler(CallbackQueryHandler(menu_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Serveur Webhook (Render)
    port = int(os.environ.get("PORT", 8443))
    print(f"🚀 Serveur Telegram lancé sur le port {port}")
    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=BOT_TOKEN,
        webhook_url=f"https://telegram-bot-ycfh.onrender.com/{BOT_TOKEN}"
    )

if __name__ == "__main__":
    main()
