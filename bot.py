import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

TOKEN = "توكن_بوتك_هنا"
PASSWORD = "7474"

authorized_users = set()

bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer("🔐 أهلاً بك\nأدخل كلمة السر للمتابعة")


@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()

    if user_id not in authorized_users:
        if text == PASSWORD:
            authorized_users.add(user_id)
            await message.answer("✅ تم الدخول\nاكتب اسم المؤسسة")
        else:
            await message.answer("❌ كلمة السر غير صحيحة")
        return

    await message.answer(f"📂 تم استلام: {text}")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
