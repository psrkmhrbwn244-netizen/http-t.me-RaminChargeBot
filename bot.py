import os
import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

ADMIN_ID = 8394005895   # آیدی عددی تو
WALLET_FILE = "wallet.json"

# ساخت فایل کیف پول اگر وجود نداشت
if not os.path.exists(WALLET_FILE):
    with open(WALLET_FILE, "w") as f:
        json.dump({}, f)

def load_wallet():
    with open(WALLET_FILE, "r") as f:
        return json.load(f)

def save_wallet(data):
    with open(WALLET_FILE, "w") as f:
        json.dump(data, f)

# ------------------ دستورات ------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["ثبت سفارش شارژ"], ["کیف پول من"]]
    await update.message.reply_text(
        "سلام رامین! ربات شارژ آماده‌ست.",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    data = load_wallet()
    balance = data.get(user_id, 0)
    await update.message.reply_text(f"موجودی شما: {balance} افغانی")

async def add_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return await update.message.reply_text("فقط ادمین می‌تواند موجودی اضافه کند.")

    try:
        user_id, amount = update.message.text.split()[1:]
        amount = int(amount)

        data = load_wallet()
        data[user_id] = data.get(user_id, 0) + amount
        save_wallet(data)

        await update.message.reply_text("موجودی با موفقیت افزایش یافت.")
    except:
        await update.message.reply_text("فرمت درست:\n/addbalance USERID مبلغ")

async def order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("شماره مورد نظر را وارد کنید:")
    context.user_data["step"] = "number"

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = str(update.message.from_user.id)

    # مرحله شماره
    if context.user_data.get("step") == "number":
        context.user_data["number"] = text
        context.user_data["step"] = "amount"
        return await update.message.reply_text("مبلغ شارژ را وارد کنید:")

    # مرحله مبلغ
    if context.user_data.get("step") == "amount":
        try:
            amount = int(text)
        except:
            return await update.message.reply_text("مبلغ باید عدد باشد.")

        data = load_wallet()
        balance = data.get(user_id, 0)

        if balance < amount:
            return await update.message.reply_text("❌ موجودی کافی نیست.")

        # کم کردن موجودی
        data[user_id] = balance - amount
        save_wallet(data)

        # ارسال سفارش برای ادمین
        await context.bot.send_message(
            ADMIN_ID,
            f"📌 سفارش جدید:\nشماره: {context.user_data['number']}\nمبلغ: {amount}\nکاربر: {user_id}"
        )

        context.user_data["step"] = None
        return await update.message.reply_text("✔ سفارش ثبت شد.")

    # دکمه‌ها
    if text == "کیف پول من":
        return await wallet(update, context)

    if text == "ثبت سفارش شارژ":
        return await order(update, context)

# ------------------ اجرای ربات ------------------

app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("addbalance", add_balance))
app.add_handler(MessageHandler(filters.TEXT, message_handler))

app.run_polling()
