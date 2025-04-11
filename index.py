from telegram import Update from telegram.ext import ( ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ChatMemberHandler ) import time import json import os

BOT_TOKEN = "7059448299:AAGTyg3EIlnQNe91LH49yWojUjHLj9HPqx4" ADMIN_FILE = "admins.json" PRIMARY_ADMIN = 7059448299 start_time = time.time()

WELCOME_MESSAGE = """ ━━━━━━━━━━━━━━ 🌟 Commandes disponibles : ╭─╼━━━━━━━━╾─╮ │ /help - Aide │ /uptime - Temps actif │ /admin - Gérer les admins │ /notify - Msg tous les admins │ /request - Demande admin │ /admin-list - Liste des admins ╰─━━━━━━━━━╾─╯ ━━━━━━━━━━━━━━ """

requests_pending = {}

def load_admins(): if not os.path.exists(ADMIN_FILE): with open(ADMIN_FILE, 'w') as f: json.dump([PRIMARY_ADMIN], f) with open(ADMIN_FILE, 'r') as f: return json.load(f)

def save_admins(admins): with open(ADMIN_FILE, 'w') as f: json.dump(admins, f)

ADMINS = load_admins() PENDING_REMOVALS = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text(WELCOME_MESSAGE)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text(WELCOME_MESSAGE)

async def uptime(update: Update, context: ContextTypes.DEFAULT_TYPE): uptime_seconds = int(time.time() - start_time) h, m, s = uptime_seconds // 3600, (uptime_seconds % 3600) // 60, uptime_seconds % 60 await update.message.reply_text(f"Uptime: {h}h {m}m {s}s")

async def admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = update.message.from_user.id if user_id not in ADMINS: await update.message.reply_text("Tu n'es pas admin.") return

if not context.args:
    await update.message.reply_text("Usage: /admin [add/remove/list] [ID]")
    return

cmd = context.args[0]
if cmd == "list":
    text = "Admins:\n" + "\n".join(
        [f"- {aid}" + (" (principal)" if aid == PRIMARY_ADMIN else "") for aid in ADMINS]
    )
    await update.message.reply_text(text)

elif cmd == "add" and len(context.args) >= 2:
    try:
        new_id = int(context.args[1])
        if new_id not in ADMINS:
            ADMINS.append(new_id)
            save_admins(ADMINS)
            await update.message.reply_text(f"Admin ajouté: {new_id}")
        else:
            await update.message.reply_text("Cet ID est déjà admin.")
    except:
        await update.message.reply_text("ID invalide.")

elif cmd == "remove" and len(context.args) >= 2:
    try:
        rem_id = int(context.args[1])
        if rem_id == PRIMARY_ADMIN:
            await update.message.reply_text("Impossible de supprimer l’admin principal.")
        elif rem_id in ADMINS:
            PENDING_REMOVALS[user_id] = rem_id
            await update.message.reply_text(
                f"Es-tu sûr de vouloir supprimer {rem_id} ? Réponds par 'oui' ou 'non'."
            )
        else:
            await update.message.reply_text("Cet ID n’est pas admin.")
    except:
        await update.message.reply_text("ID invalide.")
else:
    await update.message.reply_text("Commande invalide. Utilise: add, remove, list")

async def notify(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = update.message.from_user.id if user_id not in ADMINS: await update.message.reply_text("Seuls les admins peuvent utiliser cette commande.") return

if context.args:
    message = " ".join(context.args)
    for admin_id in ADMINS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=f"[Notification admin]\n{message}")
        except:
            pass
    await update.message.reply_text("Notification envoyée aux admins.")
else:
    await update.message.reply_text("Utilisation : /notify [message]")

async def request_admin(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = update.message.from_user.id msg = " ".join(context.args) if context.args else "(aucun message)" requests_pending[user_id] = msg for admin_id in ADMINS: await context.bot.send_message( chat_id=admin_id, text=f"Demande d'administration\nUID: {user_id}\nMessage: {msg}" ) await update.message.reply_text("Demande envoyée aux admins.")

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = update.message.from_user.id if user_id not in ADMINS: return

if len(context.args) >= 1:
    try:
        new_admin_id = int(context.args[0])
        msg = " ".join(context.args[1:]) if len(context.args) > 1 else "Bienvenue dans l'équipe."
        if new_admin_id not in ADMINS:
            ADMINS.append(new_admin_id)
            save_admins(ADMINS)
            await context.bot.send_message(chat_id=new_admin_id, text=f"Tu es maintenant admin !\n{msg}")
            await update.message.reply_text("Admin ajouté avec succès.")
        else:
            await update.message.reply_text("Cette personne est déjà admin.")
    except:
        await update.message.reply_text("Format invalide.")
else:
    await update.message.reply_text("Usage: /approve [UID] [message]")

async def admin_list(update: Update, context: ContextTypes.DEFAULT_TYPE): lines = [] for aid in ADMINS: try: user = await context.bot.get_chat(aid) name = user.full_name except: name = "Inconnu" tag = " (principal)" if aid == PRIMARY_ADMIN else "" lines.append(f"- {name} ({aid}){tag}") await update.message.reply_text("Liste des admins:\n" + "\n".join(lines))

async def group_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE): if update.my_chat_member and update.my_chat_member.new_chat_member.status == "administrator": chat = update.effective_chat await context.bot.send_message(chat_id=chat.id, text=f"Merci de m'avoir ajouté comme admin dans {chat.title} !")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE): text = update.message.text.lower() user_id = update.message.from_user.id

if user_id in PENDING_REMOVALS:
    if text == "oui":
        rem_id = PENDING_REMOVALS.pop(user_id)
        ADMINS.remove(rem_id)
        save_admins(ADMINS)
        await update.message.reply_text(f"Admin {rem_id} supprimé.")
    elif text == "non":
        PENDING_REMOVALS.pop(user_id)
        await update.message.reply_text("Suppression annulée.")
    else:
        await update.message.reply_text("Réponds avec 'oui' ou 'non'.")
    return

if text == "help":
    await help_command(update, context)
elif text == "uptime":
    await uptime(update, context)
elif text == "admin":
    await admin_handler(update, context)

def main(): app = ApplicationBuilder().token(BOT_TOKEN).build() app.add_handler(CommandHandler("start", start)) app.add_handler(CommandHandler("help", help_command)) app.add_handler(CommandHandler("uptime", uptime)) app.add_handler(CommandHandler("admin", admin_handler)) app.add_handler(CommandHandler("notify", notify)) app.add_handler(CommandHandler("request", request_admin)) app.add_handler(CommandHandler("approve", approve)) app.add_handler(CommandHandler("admin-list", admin_list)) app.add_handler(ChatMemberHandler(group_welcome, ChatMemberHandler.MY_CHAT_MEMBER)) app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

print("Bot lancé...")
app.run_polling()

if name == "main": main()

