# main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from handlers.common import start_handler, cancel_handler
from handlers.data_handlers import data_handler, staff_callback_handler, staff_handler
from handlers.event_handlers import (
    create_handler, create_event_staff_handler, event_type_handler,
    back_to_staff_handler, process_date, process_time
)
from states.states import EventStates

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Создаем объекты бота и диспетчера
storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)

# Регистрируем обработчики
def register_handlers():
    # Команды и основные обработчики
    dp.message.register(start_handler, Command("start"))
    dp.message.register(data_handler, Command("data"))
    dp.message.register(data_handler, F.text == "📊 Получить данные")
    dp.message.register(create_handler, Command("create"))
    dp.message.register(create_handler, F.text == "➕ Создать событие")
    dp.message.register(staff_handler, F.text == "⭐ ОПВУ")
    dp.message.register(cancel_handler, F.text == "❌ Отмена")
    
    # Callback обработчики
    dp.callback_query.register(staff_callback_handler, F.data.startswith("staff_"))
    dp.callback_query.register(create_event_staff_handler, F.data.startswith("create_"))
    dp.callback_query.register(event_type_handler, F.data.startswith("event_"))
    dp.callback_query.register(back_to_staff_handler, F.data == "back_to_staff")
    
    # FSM обработчики
    dp.message.register(process_date, EventStates.waiting_for_date)
    dp.message.register(process_time, EventStates.waiting_for_time)

async def main():
    """Главная функция для запуска бота"""
    try:
        print("🤖 Запуск бота...")
        register_handlers()
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Error starting bot: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())