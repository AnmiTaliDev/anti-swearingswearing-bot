import logging
import re
import asyncio
from aiogram import Bot, Dispatcher, types

# Замените "YOUR_TELEGRAM_BOT_TOKEN" на действительный токен вашего бота
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

# Путь к файлу со словами для модерации
WORDS_FILE = "words.txt"

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def load_banned_patterns():
    """
    Загружает запрещенные слова или шаблоны из файла WORDS_FILE и преобразует их в регулярные выражения.
    Поддерживаются wildcard символы: символ '*' заменяется на '.*' для соответствия любым символам.
    """
    patterns = []
    try:
        with open(WORDS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                word = line.strip()
                if word and not word.startswith("#"):
                    # Экранируем спецсимволы, затем заменяем '*' на '.*'
                    regex_pattern = re.escape(word).replace(r"\*", ".*")
                    patterns.append(re.compile(regex_pattern, re.IGNORECASE))
    except Exception as e:
        logger.error("Ошибка при загрузке файла '%s': %s", WORDS_FILE, e)
    return patterns

banned_patterns = load_banned_patterns()

# Инициализация бота и диспетчера (aiogram v3)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message()
async def moderate_message(message: types.Message):
    """
    Обработчик входящих текстовых сообщений.
    Если текст сообщения содержит запрещённые слова или шаблоны, бот:
    1. Отправляет уведомление с указанием пользователя и смайликами.
    2. Удаляет сообщение.
    Бот не банит и не мутит пользователя.
    """
    text = message.text
    if text:
        for pattern in banned_patterns:
            if pattern.search(text):
                try:
                    # Определяем имя пользователя: username или first_name
                    user = message.from_user.username if message.from_user and message.from_user.username else message.from_user.first_name
                    response_text = f"🚫 Удалено сообщение от @{user} за мат 😡"
                    # Отправляем уведомление в чат
                    await bot.send_message(chat_id=message.chat.id, text=response_text)
                    # Удаляем сообщение пользователя
                    await message.delete()
                    logger.info("Удалено сообщение %s от пользователя %s (username: %s) по шаблону '%s'",
                                message.message_id,
                                message.from_user.id if message.from_user else "Unknown",
                                user,
                                pattern.pattern)
                except Exception as e:
                    logger.error("Ошибка обработки сообщения %s: %s", message.message_id, e)
                break

async def main():
    logger.info("Бот запущен. Ожидание сообщений...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())