import os
import time
import json
from typing import Dict, List
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# Configuration
BOT_TOKEN = "7059448299:AAGTyg3EIlnQNe91LH49yWojUjHLj9HPqx4"
ADMIN_FILE = "admins.json"
REQUEST_FILE = "requests.json"
PRIMARY_ADMIN = 6100575282  # Remplacez par votre ID admin principal

# Messages
WELCOME_MSG = """
🌟 Commandes disponibles :
/help - Affiche ce message
/uptime - Voir le temps de fonctionnement
/uid - Afficher votre ID Telegram
/request [raison] - Demander les droits admin
/adminlist - Liste des admins (admin seulement)
"""

ADMIN_MSG = """
🔧 Commandes Admin :
/approve [id] [msg] - Approuver une demande
/reject [id] [msg] - Rejeter une demande
/requests - Voir les demandes
/notify [msg] - Notifier tous les admins
/admin [add/remove/list] [id] - Gérer les admins
"""

# Fonctions de gestion des données
def load_data(filename: str, default=None):
    if not os.path.exists(filename):
        with open(filename, 'w') as f:
            json.dump(default if default is not None else [], f)
    with open(filename, 'r') as f:
        return json.load(f)

def save_data(data, filename: str):
    with open(filename, 'w') as f:
        json.dump(data, f)

# Chargement des données
ADMINS = load_data(ADMIN_FILE, [PRIMARY_ADMIN])
REQUESTS = load_data(REQUEST_FILE, {})
bot_start_time = time.time()

# Handlers de commandes
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type == "private":
        await update.message.reply_text(WELCOME_MSG)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    msg = WELCOME_MSG + (ADMIN_MSG if user_id in ADMINS else "")
    await update.message.reply_text(msg)

async def uptime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uptime_sec = int(time.time() - bot_start_time)
    hours, mins, secs = uptime_sec//3600, (uptime_sec%3600)//60, uptime_sec%60
    await update.message.reply_text(f"⏱ Uptime: {hours}h {mins}m {secs}s")

async def get_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    await update.message.reply_text(
        f"🔍 Vos informations :\n"
        f"👤 Nom : {user.full_name}\n"
        f"🆔 ID : <code>{user.id}</code>\n"
        f"📛 Username : @{user.username if user.username else 'N/A'}\n\n"
        f"Cet ID est utile pour les demandes admin.",
        parse_mode='HTML'
    )

async def admin_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMINS:
        return
    admins_list = "\n".join([f"- {aid}" + (" (principal)" if aid == PRIMARY_ADMIN else "") for aid in ADMINS])
    await update.message.reply_text(f"📋 Admins:\n{admins_list}")

async def request_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    if user_id in ADMINS:
        await update.message.reply_text("✅ Vous êtes déjà admin!")
        return
        
    if not context.args:
        await update.message.reply_text("Usage: /request [votre message]")
        return
    
    REQUESTS[str(user_id)] = {
        "message": " ".join(context.args),
        "username": update.message.from_user.username or update.message.from_user.full_name,
        "timestamp": time.time()
    }
    save_data(REQUESTS, REQUEST_FILE)
    
    # Notification aux admins
    for admin_id in ADMINS:
        try:
            await context.bot.send_message(
                admin_id,
                f"⚠️ Nouvelle demande admin:\n"
                f"User: @{REQUESTS[str(user_id)]['username']}\n"
                f"ID: {user_id}\n"
                f"Message: {REQUESTS[str(user_id)]['message']}\n\n"
                f"✅ /approve {user_id}\n"
                f"❌ /reject {user_id}"
            )
        except:
            continue
    
    await update.message.reply_text("📩 Demande envoyée aux admins!")

async def approve_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMINS:
        return
        
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /approve [user_id] [message optionnel]")
        return
    
    try:
        user_id = int(context.args[0])
        if str(user_id) not in REQUESTS:
            await update.message.reply_text("❌ Aucune demande trouvée")
            return
            
        # Ajout comme admin
        if user_id not in ADMINS:
            ADMINS.append(user_id)
            save_data(ADMINS, ADMIN_FILE)
        
        # Message de confirmation
        msg = " ".join(context.args[1:]) if len(context.args) > 1 else "✅ Votre demande admin a été approuvée!"
        try:
            await context.bot.send_message(user_id, msg)
        except:
            pass
            
        # Suppression de la demande
        del REQUESTS[str(user_id)]
        save_data(REQUESTS, REQUEST_FILE)
        
        await update.message.reply_text(f"✅ Utilisateur {user_id} ajouté aux admins!")
    except ValueError:
        await update.message.reply_text("❌ ID invalide")

async def reject_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMINS:
        return
        
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /reject [user_id] [message optionnel]")
        return
    
    try:
        user_id = int(context.args[0])
        if str(user_id) not in REQUESTS:
            await update.message.reply_text("❌ Aucune demande trouvée")
            return
            
        # Message de rejet
        msg = " ".join(context.args[1:]) if len(context.args) > 1 else "❌ Votre demande admin a été rejetée"
        try:
            await context.bot.send_message(user_id, msg)
        except:
            pass
            
        # Suppression de la demande
        del REQUESTS[str(user_id)]
        save_data(REQUESTS, REQUEST_FILE)
        
        await update.message.reply_text(f"✅ Demande de {user_id} rejetée!")
    except ValueError:
        await update.message.reply_text("❌ ID invalide")

async def list_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMINS:
        return
        
    if not REQUESTS:
        await update.message.reply_text("✅ Aucune demande en attente")
        return
    
    requests_list = []
    for uid, data in REQUESTS.items():
        requests_list.append(
            f"👤 {data['username']} (ID: {uid})\n"
            f"📝 {data['message']}\n"
            f"⏰ {time.ctime(data['timestamp'])}\n"
            f"✅ /approve {uid} | ❌ /reject {uid}\n"
        )
    
    await update.message.reply_text("📨 Demandes en attente:\n\n" + "\n".join(requests_list))

async def notify_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMINS:
        return
        
    if not context.args:
        await update.message.reply_text("Usage: /notify [message]")
        return
    
    message = " ".join(context.args)
    for admin_id in ADMINS:
        try:
            await context.bot.send_message(admin_id, f"📢 Notification admin:\n{message}")
        except:
            continue
    
    await update.message.reply_text("📢 Notification envoyée à tous les admins")

async def manage_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in ADMINS:
        return
        
    if not context.args:
        await update.message.reply_text("Usage: /admin [add/remove/list] [user_id]")
        return
    
    cmd = context.args[0].lower()
    
    if cmd == "list":
        await admin_list(update, context)
    
    elif cmd == "add" and len(context.args) > 1:
        try:
            new_admin = int(context.args[1])
            if new_admin not in ADMINS:
                ADMINS.append(new_admin)
                save_data(ADMINS, ADMIN_FILE)
                await update.message.reply_text(f"✅ Admin {new_admin} ajouté")
            else:
                await update.message.reply_text("⚠️ Cet utilisateur est déjà admin")
        except ValueError:
            await update.message.reply_text("❌ ID invalide")
    
    elif cmd == "remove" and len(context.args) > 1:
        try:
            admin_id = int(context.args[1])
            if admin_id == PRIMARY_ADMIN:
                await update.message.reply_text("❌ Impossible de supprimer l'admin principal")
            elif admin_id in ADMINS:
                ADMINS.remove(admin_id)
                save_data(ADMINS, ADMIN_FILE)
                await update.message.reply_text(f"✅ Admin {admin_id} supprimé")
            else:
                await update.message.reply_text("❌ Cet utilisateur n'est pas admin")
        except ValueError:
            await update.message.reply_text("❌ ID invalide")
    
    else:
        await update.message.reply_text("❌ Commande invalide")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Commandes utilisateur
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("uptime", uptime))
    app.add_handler(CommandHandler("uid", get_user_id))  # Nouvelle commande uid
    app.add_handler(CommandHandler("request", request_admin))
    app.add_handler(CommandHandler("adminlist", admin_list))
    
    # Commandes admin
    app.add_handler(CommandHandler("approve", approve_request))
    app.add_handler(CommandHandler("reject", reject_request))
    app.add_handler(CommandHandler("requests", list_requests))
    app.add_handler(CommandHandler("notify", notify_admins))
    app.add_handler(CommandHandler("admin", manage_admins))
    
    # Lancement du bot
    app.run_polling()

if __name__ == "__main__":
    main()
