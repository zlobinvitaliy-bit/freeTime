import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Tuple
import fdb
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import F

# Настройки
BOT_TOKEN = "5547644775:AAFJ_k6mnKq3bJESW-S5vw9YpixmZ313yk8"  # Замените на ваш токен бота
DB_HOST = "10.15.0.40"  # Хост базы данных
DB_PATH = "E:\\Perco\\SCD17K#.FDB"  # Путь к базе данных
DB_USER = "SYSDBA"  # Пользователь базы данных
DB_PASSWORD = "GpjT7M41"  # Пароль базы данных

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Создаем объекты бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ID пользователей для мониторинга
STAFF_IDS = {
    "Wallace": 63736,
    "Zlo": 7419,
    "Formoza": 63763
}

class DatabaseManager:
    def __init__(self):
        self.connection_string = f"{DB_HOST}:{DB_PATH}"
        
    def get_connection(self):
        """Создает подключение к базе данных Firebird"""
        return fdb.connect(
            dsn=self.connection_string,
            user=DB_USER,
            password=DB_PASSWORD,
            charset='UTF8'
        )
    
    def get_intermediate_data(self, staff_id: int) -> List[Tuple]:
        """Получает данные из таблицы TABEL_INTERMEDIADATE за последние 2 дня"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Дата два дня назад
            two_days_ago = datetime.now().date() - timedelta(days=2)
            
            query = """
            SELECT TIME_PASS, DATE_PASS, TYPE_PASS
            FROM TABEL_INTERMEDIADATE 
            WHERE STAFF_ID = ? 
            AND DATE_PASS >= ?
            ORDER BY DATE_PASS DESC, TIME_PASS DESC
            """
            
            cursor.execute(query, (staff_id, two_days_ago))
            return cursor.fetchall()
    
    def get_reg_events_data(self, staff_id: int) -> List[Tuple]:
        """Получает данные из таблицы REG_EVENTS за последние 2 дня"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Дата два дня назад
            two_days_ago = datetime.now().date() - timedelta(days=2)
            
            query = """
            SELECT DATE_EV, TIME_EV, AREAS_ID, LAST_TIMESTAMP
            FROM REG_EVENTS 
            WHERE STAFF_ID = ? 
            AND DATE_EV >= ?
            AND AREAS_ID IN (25376, 1)
            ORDER BY DATE_EV DESC, TIME_EV DESC
            """
            
            cursor.execute(query, (staff_id, two_days_ago))
            return cursor.fetchall()

db_manager = DatabaseManager()

def format_intermediate_data(data: List[Tuple], staff_name: str) -> str:
    """Форматирует данные из таблицы TABEL_INTERMEDIADATE"""
    if not data:
        return f"📊 <b>Данные по {staff_name} (TABEL_INTERMEDIADATE)</b>\n\nДанных за последние 2 дня не найдено."
    
    message = f"📊 <b>Данные по {staff_name} (TABEL_INTERMEDIADATE)</b>\n\n"
    
    current_date = None
    for time_pass, date_pass, type_pass in data:
        # Группировка по дням
        if current_date != date_pass:
            current_date = date_pass
            message += f"📅 <b>{date_pass.strftime('%d.%m.%Y')}</b>\n"
        
        # Определяем тип прохода
        pass_type = "🟢 Вход" if type_pass == 1 else "🔴 Выход"
        
        message += f"  {time_pass.strftime('%H:%M:%S')} - {pass_type}\n"
    
    return message

def format_reg_events_data(data: List[Tuple], staff_name: str) -> str:
    """Форматирует данные из таблицы REG_EVENTS"""
    if not data:
        return f"📋 <b>Данные по {staff_name} (REG_EVENTS)</b>\n\nДанных за последние 2 дня не найдено."
    
    message = f"📋 <b>Данные по {staff_name} (REG_EVENTS)</b>\n\n"
    
    current_date = None
    for date_ev, time_ev, areas_id, last_timestamp in data:
        # Группировка по дням
        if current_date != date_ev:
            current_date = date_ev
            message += f"📅 <b>{date_ev.strftime('%d.%m.%Y')}</b>\n"
        
        # Определяем тип по AREAS_ID
        area_type = "🟢 Вход" if areas_id == 25376 else "🔴 Выход"
        
        # Форматируем LAST_TIMESTAMP если он есть
        timestamp_str = ""
        if last_timestamp:
            timestamp_str = f" (TS: {last_timestamp.strftime('%H:%M:%S')})"
        
        message += f"  {time_ev.strftime('%H:%M:%S')} - {area_type}{timestamp_str}\n"
    
    return message

def create_staff_keyboard():
    """Создает клавиатуру для выбора сотрудника"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=name, callback_data=f"staff_{staff_id}")]
        for name, staff_id in STAFF_IDS.items()
    ])
    return keyboard

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    """Обработчик команды /start"""
    welcome_text = """
👋 Добро пожаловать в бот мониторинга проходов!

Этот бот поможет вам получить информацию о проходах сотрудников за последние 2 дня.

Доступные команды:
/data - Получить данные по сотруднику
/help - Показать эту справку

Выберите сотрудника для получения данных:
    """
    
    await message.answer(welcome_text, reply_markup=create_staff_keyboard(), parse_mode="HTML")

@dp.message(Command("data"))
async def data_handler(message: types.Message):
    """Обработчик команды /data"""
    await message.answer(
        "👥 Выберите сотрудника для получения данных за последние 2 дня:",
        reply_markup=create_staff_keyboard()
    )

@dp.message(Command("help"))
async def help_handler(message: types.Message):
    """Обработчик команды /help"""
    help_text = """
🤖 <b>Справка по боту</b>

<b>Команды:</b>
/start - Начать работу с ботом
/data - Получить данные по сотруднику
/help - Показать эту справку

<b>Функции:</b>
• Получение данных из таблицы TABEL_INTERMEDIADATE
• Получение данных из таблицы REG_EVENTS
• Отображение данных за последние 2 дня
• Информация о входах и выходах

<b>Обозначения:</b>
🟢 - Вход
🔴 - Выход
📊 - Данные из TABEL_INTERMEDIADATE
📋 - Данные из REG_EVENTS
    """
    
    await message.answer(help_text, parse_mode="HTML")

@dp.callback_query(F.data.startswith("staff_"))
async def staff_callback_handler(callback_query: types.CallbackQuery):
    """Обработчик выбора сотрудника"""
    staff_id = int(callback_query.data.split("_")[1])
    staff_name = next(name for name, id in STAFF_IDS.items() if id == staff_id)
    
    await callback_query.message.edit_text("⏳ Получаю данные...")
    
    try:
        # Получаем данные из обеих таблиц
        intermediate_data = db_manager.get_intermediate_data(staff_id)
        reg_events_data = db_manager.get_reg_events_data(staff_id)
        
        # Форматируем данные
        intermediate_message = format_intermediate_data(intermediate_data, staff_name)
        reg_events_message = format_reg_events_data(reg_events_data, staff_name)
        
        # Отправляем два отдельных сообщения
        await callback_query.message.edit_text(intermediate_message, parse_mode="HTML")
        await callback_query.message.answer(reg_events_message, parse_mode="HTML")
        
        # Добавляем кнопку для повторного выбора
        await callback_query.message.answer(
            "Выберите другого сотрудника:",
            reply_markup=create_staff_keyboard()
        )
        
    except Exception as e:
        error_message = f"❌ Ошибка при получении данных: {str(e)}"
        await callback_query.message.edit_text(error_message)
        logging.error(f"Database error: {e}")
    
    await callback_query.answer()

async def main():
    """Главная функция для запуска бота"""
    try:
        print("🤖 Запуск бота...")
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Error starting bot: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())