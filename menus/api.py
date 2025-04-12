import requests
import os
import time
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Configuration des URLs API
API_URLS = {
    "webinfo": "https://jonell01-ccprojectsapihshs.hf.space/api/webinfo?url=",
    "ghibli": "https://jonell01-ccprojectsapihshs.hf.space/api/ghibli?url=",
    "deepseek": "https://jonell01-ccprojectsapihshs.hf.space/api/deepseek-r1?ask="
}

# Dossier pour stocker temporairement les images
IMG_DIR = "IMG"
if not os.path.exists(IMG_DIR):
    os.makedirs(IMG_DIR)

async def handle_webinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(
            text="🌐 Veuillez envoyer une URL à analyser (ex: https://example.com)",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Retour", callback_data="main_menu")]
            ])
        )
    else:
        await update.message.reply_text(
            "🌐 Veuillez envoyer une URL à analyser (ex: https://example.com)",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Retour", callback_data="main_menu")]
            ])
        )
    context.user_data["current_function"] = "webinfo"

async def handle_ghibli(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(
            text="🎨 Envoyez une image à traiter avec Ghibli Studio",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Retour", callback_data="main_menu")]
            ])
        )
    else:
        await update.message.reply_text(
            "🎨 Envoyez une image à traiter avec Ghibli Studio",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Retour", callback_data="main_menu")]
            ])
        )
    context.user_data["current_function"] = "ghibli"

async def handle_deepseek(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(
            text="🤖 Posez votre question à DeepSeek",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Retour", callback_data="main_menu")]
            ])
        )
    else:
        await update.message.reply_text(
            "🤖 Posez votre question à DeepSeek",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Retour", callback_data="main_menu")]
            ])
        )
    context.user_data["current_function"] = "deepseek"

async def process_webinfo(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    try:
        response = requests.get(API_URLS["webinfo"] + url)
        if response.status_code == 200:
            await update.message.reply_text(f"🌐 Résultat d'analyse:\n{response.text}")
        else:
            await update.message.reply_text("❌ Erreur lors de l'analyse de l'URL")
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur: {str(e)}")

async def process_ghibli(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("❌ Veuillez envoyer une image valide")
        return
    
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    filename = f"{IMG_DIR}/{photo.file_id}.jpg"
    
    await file.download_to_drive(filename)
    
    try:
        with open(filename, 'rb') as img_file:
            response = requests.post(API_URLS["ghibli"], files={'file': img_file})
        
        if response.status_code == 200:
            await update.message.reply_text(f"🎨 Résultat du traitement:\n{response.text}")
        else:
            await update.message.reply_text("❌ Erreur lors du traitement de l'image")
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur: {str(e)}")
    finally:
        # Suppression différée du fichier
        time.sleep(60)
        if os.path.exists(filename):
            os.remove(filename)

async def process_deepseek(update: Update, context: ContextTypes.DEFAULT_TYPE, question: str):
    try:
        response = requests.get(API_URLS["deepseek"] + question)
        if response.status_code == 200:
            await update.message.reply_text(f"🤖 Réponse de DeepSeek:\n{response.text}")
        else:
            await update.message.reply_text("❌ Erreur lors de la requête à DeepSeek")
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur: {str(e)}")

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🌐 Web-Info", callback_data="webinfo")],
        [InlineKeyboardButton("🎨 Ghibli Studio", callback_data="ghibli")],
        [InlineKeyboardButton("🤖 GPT40", callback_data="deepseek")],
        [InlineKeyboardButton("🆘 Aide", callback_data="help")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text="🌟 Menu Principal - Choisissez une fonctionnalité:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            text="🌟 Menu Principal - Choisissez une fonctionnalité:",
            reply_markup=reply_markup
  )
