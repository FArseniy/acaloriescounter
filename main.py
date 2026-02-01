import asyncio
import io
import os
import google.generativeai as genai
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from PIL import Image

# БЕРЕМ КЛЮЧИ ИЗ ОКРУЖЕНИЯ (БЕЗОПАСНО)
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TG_BOT_TOKEN or not GEMINI_API_KEY:
    raise ValueError("❌ ОШИБКА: Не найдены ключи в .env файле!")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
bot = Bot(token=TG_BOT_TOKEN)
dp = Dispatcher()

SYSTEM_PROMPT = """
Ты профессиональный диетолог. 
1. Определи блюдо.
2. Оцени вес.
3. Посчитай КБЖУ (Калории, Белки, Жиры, Углеводы).
Ответ в формате:
🍽 **Блюдо:** ...
⚖️ **Вес:** ...
🔥 **Ккал:** ... | 🥩 **Б:** ... | 🥑 **Ж:** ... | 🍞 **У:** ...
"""

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Привет! Отправь фото еды 🍏")

@dp.message(F.photo)
async def handle_photo(message: Message):
    msg = await message.answer("🔍 Смотрю...")
    try:
        photo = message.photo[-1]
        file_io = io.BytesIO()
        await bot.download(photo, destination=file_io)
        file_io.seek(0)
        image = Image.open(file_io)
        response = model.generate_content([SYSTEM_PROMPT, image])
        await msg.edit_text(response.text, parse_mode="Markdown")
    except Exception as e:
        await msg.edit_text(f"Ошибка: {e}")

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())