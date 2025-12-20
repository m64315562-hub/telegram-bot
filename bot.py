from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

TOKEN = "8388460961:AAEPh06c0C_pbtf-XeA81QLJKhR2FyO-HIU"
PASSWORD = "7474"

authorized = set()

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_id not in authorized:
        if text == PASSWORD:
            authorized.add(user_id)
            await update.message.reply_text("✅ تم الدخول\nاكتب اسم المؤسسة")
        else:
            await update.message.reply_text("🔒 أدخل كلمة السر")
        return

    await update.message.reply_text(f"📂 استلمت: {text}")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
app.run_polling()
