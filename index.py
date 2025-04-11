from telegram import Update from telegram.ext import ( ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes ) import time import json import os

BOT_TOKEN = "7059448299:AAGTyg3EIlnQNe91LH49yWojUjHLj9HPqx4" ADMIN_FILE = "admins.json" REQUEST_FILE = "requests.json" PRIMARY_ADMIN = 7059448299  # Remplace par ton propre ID start_time = time.time()

WELCOME_MESSAGE = """ ━━━━━━━━━━━━━━ 🌟 Commandes disponibles : ╭─╼━━━━━━━━╾─╮ │ /help - Aide │ /uptime - Temps actif │ /admin - Gérer les admins │ /notify - Message à tous les admins │ /admin-list - Liste des admins │ /uid - Ton ID Telegram │ /request [message] - Demander à devenir admin ╰─━━━━━━━━━╾─╯ ━━━━━━━━━━━━━━ """

def load_json(file_path, default): if not os.path.exists(file_path): with open(file_path, 'w') as f: json.dump(default, f) with open(file_path, 'r') as f: return json.load(f)

def save_json(file_path, data): with open(file_path, 'w') as f: json.dump(data, f)

ADMINS = load_json(ADMIN_FILE, [PRIMARY_ADMIN]) REQUESTS = load_json(REQUEST_FILE, {}) PENDING_REMOVALS = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text(WELCOME_MESSAGE)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text(WELCOME_MESSAGE)

async def uptime(update: Update, context: ContextTypes.DEFAULT_TYPE): uptime_seconds = int(time.time() - start_time) h, m, s = uptime_seconds // 3600, (uptime_seconds % 3600) // 60, uptime_seconds % 60 await update.message.reply_text(f"Uptime: {h}h {m}m {s}s")

async def uid(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text(f"Ton UID est : {update.message.from_user.id}")

async def admin_list(update: Update, context: ContextTypes.DEFAULT_TYPE): text = "Admins:\n" for aid in ADMINS: try: user = await context.bot.get_chat(aid) name = user.full_name except: name = "(inconnu)" text += f"- {name} ({aid})\n" await update.message.reply_text(text)

async def request_admin(update: Update, context: ContextTypes.DEFAULT_TYPE): user = update.message.from_user if not context.args: await update.message.reply_text("Utilisation : /request [ton message de demande]") return msg = ' '.join(context.args) REQUESTS[str(user.id)] = { "name": user.full_name, "message": msg } save_json(REQUEST_FILE, REQUESTS) for admin_id in ADMINS: await context.bot.send_message(chat_id=admin_id, text=f"[Demande d'administration]\nDe: {user.full_name} ({user.id})\nMessage: {msg}") await update.message.reply_text("Ta demande a été envoyée aux admins.")

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = update.message.from_user.id if user_id not in ADMINS: return await update.message.reply_text("Tu n'es pas admin.")

if len(context.args) < 2:
    return await update.message.reply_text("Utilisation: /approve [uid] [message]")

uid_to_approve = int(context.args[0])
note = ' '.join(context.args[1:])

if uid_to_approve in ADMINS:
    return await update.message.reply_text("Cet utilisateur est déjà admin.")

ADMINS.append(uid_to_approve)
save_json(ADMIN_FILE, ADMINS)
await context.bot.send_message(chat_id=uid_to_approve,
    text=f"Ta demande d'administration a été approuvée !\n{note}")
await update.message.reply_text(f"{uid_to_approve} est maintenant admin.")

async def admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = update.message.from_user.id if user_id not in ADMINS: return await update.message.reply_text("Tu n'es pas admin.")

if not context.args:
    return await update.message.reply_text("Usage: /admin [add/remove/list] [ID]")

cmd = context.args[0]
if cmd == "list":
    return await admin_list(update, context)
elif cmd == "add" and len(context.args) >= 2:
    try:
        new_id = int(context.args[1])
        if new_id not in ADMINS:
            ADMINS.append(new_id)
            save_json(ADMIN_FILE, ADMINS)
            await update.message.reply_text(f"Admin ajouté: {new_id}")
        else:
            await update.message.reply_text("Cet ID est déjà admin.")
    except:
        await update.message.reply_text("ID invalide.")
elif cmd == "remove" and len(context.args) >= 2:
    try:
        rem_id = int(context.args[1])
        if rem_id == PRIMARY_ADMIN:
            return await update.message.reply_text("Impossible de supprimer l'admin principal.")
        elif rem_id in ADMINS:
            PENDING_REMOVALS[user_id] = rem_id
            await update.message.reply_text(f"Supprimer {rem_id} ? Réponds par 'oui' ou 'non'.")
        else:
            await update.message.reply_text("Cet ID n'est pas admin.")
    except:
        await update.message.reply_text("ID invalide.")
else:
    await update.message.reply_text("Commande invalide. Utilise: add, remove, list")

async def notify(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = update.message.from_user.id if user_id not in ADMINS: return await update.message.reply_text("Seuls les admins peuvent utiliser cette commande.")

if context.args:
    message = " ".join(context.args)
    for admin_id in ADMINS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=f"[Notification admin]\n{message}")
        except:
            pass
    await update.message.reply_text("Notification envoyée.")
else:
    await update.message.reply_text("Utilisation : /notify [message]")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE): text = update.message.text.lower() user_id = update.message.from_user.id

if user_id in PENDING_REMOVALS:
    if text == "oui":
        rem_id = PENDING_REMOVALS.pop(user_id)
        ADMINS.remove(rem_id)
        save_json(ADMIN_FILE, ADMINS)
        await update.message.reply_text(f"Admin {rem_id} supprimé.")
    elif text == "non":
        PENDING_REMOVALS.pop(user_id)
        await update.message.reply_text("Suppression annulée.")
    else:
        await update.message.reply_text("Réponds avec 'oui' ou 'non'.")

def main(): app = ApplicationBuilder().token(BOT_TOKEN).build() app.add_handler(CommandHandler("start", start)) app.add_handler(CommandHandler("help", help_command)) app.add_handler(CommandHandler("uptime", uptime)) app.add_handler(CommandHandler("uid", uid)) app.add_handler(CommandHandler("admin-list", admin_list)) app.add_handler(CommandHandler("request", request_admin)) app.add_handler(CommandHandler("approve", approve)) app.add_handler(CommandHandler("admin", admin_handler)) app.add_handler(CommandHandler("notify", notify)) app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler)) print("Bot lancé...") app.run_polling()

if name == "main": main()

