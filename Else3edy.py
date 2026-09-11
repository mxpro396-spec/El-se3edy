import asyncio
import json
import os
import logging
import random
from datetime import datetime
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# ========== SETTINGS ==========
BOT_TOKEN = "8617391619:AAGayjvkU0cQkweBMmDPeeRdiMAcLb61_po"
DATA_FILE = "invite_data.json"
# ==============================

logging.basicConfig(level=logging.INFO)

WAITING_FOR_LINK = 0
WAITING_FOR_COUNT = 1

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def register_invite(link):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(link, headers=headers, timeout=10)
        return response.status_code == 200
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "اهلا بك ف بوت الصعيدي .\n"
        "ادخل اللينك"
    )
    return WAITING_FOR_LINK

async def receive_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    link = update.message.text.strip()
    if not link.startswith("http://") and not link.startswith("https://"):
        await update.message.reply_text("Invalid link. Please send a valid URL starting with http:// or https://")
        return WAITING_FOR_LINK

    context.user_data["link"] = link
    context.user_data["start_time"] = datetime.now()

    await update.message.reply_text(
        "Link received successfully.\n"
        "Choose the number of registrations you want:",
        reply_markup=InlineKeyboardMarkup([
 
             [InlineKeyboardButton("5", callback_data="count_5")],
                                 [InlineKeyboardButton("10", callback_data="count_10")],
            [InlineKeyboardButton("20", callback_data="count_20")],
            [InlineKeyboardButton("30", callback_data="count_30")],
            [InlineKeyboardButton("40", callback_data="count_40")],
            [InlineKeyboardButton("50", callback_data="count_50")],
            [InlineKeyboardButton("60", callback_data="count_60")],
            [InlineKeyboardButton("Status", callback_data="status")],
        ])
    )
    return WAITING_FOR_COUNT

async def count_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "status":
        total = context.user_data.get("total_done", 0)
        await query.edit_message_text(f"{total} من 60 ")
        return WAITING_FOR_COUNT

    count = int(query.data.split("_")[1])
    link = context.user_data.get("link")
    start_time = context.user_data.get("start_time", datetime.now())

    total_done = context.user_data.get("total_done", 0)
    remaining = 60 - total_done
    if count > remaining:
        await query.edit_message_text(f"Only {remaining} left, choose a smaller number.")
        return WAITING_FOR_COUNT

    await query.edit_message_text(f"Registering {count} invites... Please wait, this may take a few minutes.")

    success = 0
    for i in range(count):
        if register_invite(link):
            success += 1
            total_done += 1
            context.user_data["total_done"] = total_done
            # Save progress
            user_data = load_data()
            user_data[str(update.effective_user.id)] = {"total": total_done, "link": link}
            save_data(user_data)

        if (i + 1) % 5 == 0 or (i + 1) == count:
            await query.edit_message_text(
                f"Registering...\nDone {i+1} of {count}\nTotal: {total_done} of 60"
            )

        if i < count - 1:
            await asyncio.sleep(random.randint(10, 20))

    end_time = datetime.now()
    duration_seconds = int((end_time - start_time).total_seconds())

    user = update.effective_user
    user_id = user.id
    username = user.username if user.username else user.first_name if user.first_name else "User"
    left = 60 - total_done

    msg = (
        "Completed Successfully\n"
        "━━━━━━━━━━━━\n"
        "▰▰▰▰▰▰▰▰▰▰▰▰\n"
        f"Done: {success}/{count}\n"
        f"Time: {duration_seconds} sec\n"
        f"Player: {username}\n"
        f"Player ID: {user_id}\n"
        "Shipment: 660 UC\n"
        f"LINK REACHED: {total_done}/60 | {left} LEFT\n"
        "by.{MX}"
    )

    if total_done >= 60:
        msg += "\n\nReward unlocked! 660 UC added to your account."

    await query.edit_message_text(msg)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Process cancelled.")
    return ConversationHandler.END

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_FOR_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_link)],
            WAITING_FOR_COUNT: [CallbackQueryHandler(count_selection, pattern="^(count_|status)")]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == "__main__":
    main()