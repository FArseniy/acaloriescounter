import asyncio
import io
import os
from google import genai # Новая библиотека
from google.genai import types
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from PIL import Image

# --- КОНФИГУРАЦИЯ ---
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TG_BOT_TOKEN or not GEMINI_API_KEY:
    raise ValueError("❌ ОШИБКА: Не найдены ключи в .env файле!")

# Инициализация клиента по-новому
client = genai.Client(api_key=GEMINI_API_KEY)

# ВЫБОР МОДЕЛИ
# Можно ставить 'gemini-2.0-flash' или 'gemini-2.5-flash' (если доступна)
MODEL_ID = 'gemini-2.0-flash' 

bot = Bot(token=TG_BOT_TOKEN)
dp = Dispatcher()

# --- ПРОМПТ ---
def get_system_prompt(user_text=None):
    user_context = ""
    if user_text:
        user_context = f"\n🚨 **ВАЖНОЕ УТОЧНЕНИЕ ОТ ПОЛЬЗОВАТЕЛЯ:** \"{user_text}\" (Используй эти данные/вес как приоритетные!)"

    return f"""
    Ты — элитный клинический нутрициолог. Твоя цель — хирургическая точность в подсчете калорий.
    
    {user_context}

    ТВОЙ АЛГОРИТМ АНАЛИЗА:
    1. **Сканирование:** Определи блюдо. Если это сложное блюдо, разбей на ингредиенты.
    2. **Скрытые калории:** Обязательно учти масло для жарки, соусы, заправки, сахар в напитках. Не занижай калорийность!
    3. **Вес:** - Если пользователь указал вес выше — считай СТРОГО на этот вес.
       - Если нет — оцени вес визуально, исходя из стандартных размеров посуды.
    4. **Расчет:** Суммируй КБЖУ всех ингредиентов.

    ФОРМАТ ОТВЕТА (Строго соблюдай Markdown):
    
    🍽 **[Название блюда]**
    ⚖️ *Вес:* `[Вес]` (укажи: визуальная оценка или по данным пользователя)
    
    ━━━━━━━━━━━━━━━━━━
    🔥 **[Ккал] ккал**
    🥩 Б: **[Белки]** • 🥑 Ж: **[Жиры]** • 🍞 У: **[Углеводы]**
    ━━━━━━━━━━━━━━━━━━
    
    📋 **Состав порции:**
    — [Ингредиент 1] (~[вес]г)
    — [Ингредиент 2] (~[вес]г)
    *(Если есть скрытые калории типа масла — укажи их тут)*

    💡 **Вердикт:** [Одно короткое предложение: полезно, сбалансировано или "калорийная бомба"]
    """

# --- ХЕНДЛЕРЫ ---

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("🚀 **Бот обновлен до Gemini 2.0!**\nКидай фото еды, посчитаю моментально.")

@dp.message(F.photo)
async def handle_photo(message: Message):
    user_caption = message.caption
    
    if user_caption:
        msg = await message.answer(f"👌 Учту: *{user_caption}*", parse_mode="Markdown")
    else:
        msg = await message.answer("👀 Сканирую...", parse_mode="Markdown")
    
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        # Подготовка фото
        photo = message.photo[-1]
        file_io = io.BytesIO()
        await bot.download(photo, destination=file_io)
        file_io.seek(0)
        
        # Для новой библиотеки конвертируем в Pillow Image
        image = Image.open(file_io)

        # ЗАПРОС (Новый синтаксис)
        prompt_text = get_system_prompt(user_caption)
        
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[prompt_text, image]
        )
        
        await msg.edit_text(response.text, parse_mode="Markdown")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        await msg.edit_text(f"⚠️ Ошибка API. Попробуй другое фото.\nОшибка: {e}")

@dp.message(F.text)
async def handle_any_text(message: Message):
    await message.answer("📸 Жду только фото еды!")

# --- ЗАПУСК ---
async def main():
    print(f"🔥 Бот запущен на новой библиотеке! Модель: {MODEL_ID}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
