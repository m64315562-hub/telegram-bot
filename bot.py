import asyncio
import sqlite3
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from PIL import Image
import pytesseract

TOKEN = os.getenv("7844115606:AAFIwGkxn5BOqhsOHPfhw3JPMIqTzz8ceeM")
PASSWORD = "7474"

bot = Bot(token=7844115606:AAFIwGkxn5BOqhsOHPfhw3JPMIqTzz8ceeM)
dp = Dispatcher()

authorized_users = set()
user_state = {}

# ------------------ قاعدة البيانات ------------------
db = sqlite3.connect("data.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    saudization INTEGER DEFAULT 0,
    saudi_name TEXT,
    licenses INTEGER DEFAULT 4,
    cards_used INTEGER DEFAULT 0
)
""")
db.commit()

# ------------------ البداية ------------------
@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer("🔐 أدخل كلمة السر للمتابعة")

# ------------------ الرسائل ------------------
@dp.message()
async def handle(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()

    # 🔐 كلمة السر
    if user_id not in authorized_users:
        if text == PASSWORD:
            authorized_users.add(user_id)
            await message.answer("✅ تم الدخول\nاكتب اسم المؤسسة")
        else:
            await message.answer("❌ كلمة السر غير صحيحة")
        return

    # 🟢 قائمة تحتاج سعودة
    if text == "سعودة":
        cursor.execute("""
        SELECT name FROM companies
        WHERE saudization = 0 OR cards_used < licenses
        """)
        rows = cursor.fetchall()
        if not rows:
            await message.answer("✅ لا توجد مؤسسات تحتاج سعودة")
            return
        msg = "📌 *المؤسسات التي تحتاج سعودة:*\n\n"
        for i, r in enumerate(rows, 1):
            msg += f"{i}- {r[0]}\n"
        await message.answer(msg, parse_mode="Markdown")
        return

    # ➕ إضافة معلومات
    if text == "➕ إضافة معلومات":
        await message.answer(
            "اختر العملية:",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[
                    [types.KeyboardButton(text="🇸🇦 تمّت السعودة")],
                    [types.KeyboardButton(text="🪪 سحب كرت عمل")],
                ],
                resize_keyboard=True
            )
        )
        return

    # 🇸🇦 السعودة
    if text == "🇸🇦 تمّت السعودة":
        user_state[user_id]["action"] = "ocr_wait"
        await message.answer("📸 أرسل صورة هوية السعودي")
        return

    # 🪪 سحب كرت عمل
    if text == "🪪 سحب كرت عمل":
        await message.answer(
            "اختر مدة كرت العمل:",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[
                    [types.KeyboardButton(text="🟢 6 أشهر"), types.KeyboardButton(text="🟢 12 شهر")],
                ],
                resize_keyboard=True
            )
        )
        return

    # ⏱️ مدة الكرت
    if text in ["🟢 6 أشهر", "🟢 12 شهر"]:
        company = user_state[user_id]["company"]
        cursor.execute("""
        UPDATE companies SET cards_used = cards_used + 1 WHERE name=?
        """, (company,))
        db.commit()
        await message.answer(f"✅ تم سحب كرت عمل لمدة {text.replace('🟢','').strip()}")
        return

    # 🏢 البحث / إنشاء مؤسسة
    cursor.execute("SELECT * FROM companies WHERE name=?", (text,))
    company = cursor.fetchone()
    if not company:
        cursor.execute("INSERT INTO companies (name) VALUES (?)", (text,))
        db.commit()
        cursor.execute("SELECT * FROM companies WHERE name=?", (text,))
        company = cursor.fetchone()

    user_state[user_id] = {"company": company[1]}

    saud = "✅" if company[2] else "❌"
    saudi_name = company[3] if company[3] else "—"
    balance = company[4] - company[5]

    await message.answer(
        f"""🏢 *{company[1]}*

📊 رصيد الاستقطاب: {balance} / {company[4]}
🇸🇦 السعودة: {saud}
👤 السعودي: {saudi_name}
🪪 كروت العمل: {company[5]} / {company[4]}
""",
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="➕ إضافة معلومات")],
                [types.KeyboardButton(text="سعودة")],
            ],
            resize_keyboard=True
        )
    )

# ------------------ OCR من صورة ------------------
@dp.message(lambda m: m.photo)
async def handle_photo(message: types.Message):
    user_id = message.from_user.id
    if user_state.get(user_id, {}).get("action") != "ocr_wait":
        return

    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    await bot.download_file(file.file_path, "id.jpg")

    text = pytesseract.image_to_string(Image.open("id.jpg"), lang="ara")
    name = text.split("\n")[0][:40]

    company = user_state[user_id]["company"]
    cursor.execute("""
    UPDATE companies SET saudization=1, saudi_name=? WHERE name=?
    """, (name, company))
    db.commit()

    await message.answer(f"✅ تم تسجيل السعودة\n👤 الاسم المستخرج:\n{name}")

# ------------------ التشغيل ------------------
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
