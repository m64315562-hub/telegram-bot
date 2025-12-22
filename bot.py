import json
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

TOKEN = "7844115606:AAFIwGkxn5BOqhsOHPfhw3JPMIqTzz8ceeM"
PASSWORD = "7474"
DATA_FILE = "data.json"

authorized_users = set()


def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔐 أدخل كلمة السر")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    data = load_data()

    # 🔐 التحقق
    if user_id not in authorized_users:
        if text == PASSWORD:
            authorized_users.add(user_id)
            await update.message.reply_text("✅ تم الدخول\nاكتب اسم المؤسسة")
        else:
            await update.message.reply_text("❌ كلمة السر غير صحيحة")
        return

    # 📌 أمر السعودة
    if text == "سعودة":
        msg = "📋 المؤسسات التي تحتاج سعودة:\n\n"
        i = 1
        for name, inst in data["institutions"].items():
            if inst["saudization"] is False and inst["work_permits"] > 0:
                msg += f"{i}- {name}\n"
                i += 1
        if i == 1:
            msg = "✅ لا توجد مؤسسات تحتاج سعودة"
        await update.message.reply_text(msg)
        return

    # 🏢 البحث / إضافة مؤسسة
    if text not in data["institutions"]:
        data["institutions"][text] = {
            "recruitment": 4,
            "work_permits": 4,
            "saudization": False
        }
        save_data(data)

    inst = data["institutions"][text]

    keyboard = [
        [
            InlineKeyboardButton(
                f"السعودة {'✅' if inst['saudization'] else '❌'}",
                callback_data=f"toggle_saud_{text}"
            )
        ],
        [
            InlineKeyboardButton(
                f"رصيد الاستقطاب: {inst['recruitment']}",
                callback_data=f"use_rec_{text}"
            )
        ],
        [
            InlineKeyboardButton(
                f"رخص العمل: {inst['work_permits']}",
                callback_data=f"use_work_{text}"
            )
        ]
    ]

    reply = (
        f"🏢 *{text}*\n"
        f"رصيد الاستقطاب: {inst['recruitment']}\n"
        f"رخص العمل: {inst['work_permits']}\n"
        f"السعودة: {'تم' if inst['saudization'] else 'لم تتم'}"
    )

    await update.message.reply_text(
        reply,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = load_data()
    action, name = query.data.split("_", 1)
    inst = data["institutions"][name]

    if action == "toggle":
        inst["saudization"] = not inst["saudization"]

    elif action == "use":
        if query.data.startswith("use_rec") and inst["recruitment"] > 0:
            inst["recruitment"] -= 1
        if query.data.startswith("use_work") and inst["work_permits"] > 0:
            inst["work_permits"] -= 1

    save_data(data)
    await query.message.reply_text(f"✅ تم تحديث بيانات {name}")


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()


if __name__ == "__main__":
    main()
