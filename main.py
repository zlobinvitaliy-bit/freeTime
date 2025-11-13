import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Tuple, Dict
import fdb
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Настройки
BOT_TOKEN = "7560155105:AAFPrs5kQukH9Y-IaEgPnimkGSe9vD0v5-U"  # Замените на ваш токен бота
DB_HOST = "127.0.0.1"  # Хост базы данных
DB_PATH = "T:\\PERCO.FDB"  # Путь к базе данных
DB_USER = "SYSDBA"  # Пользователь базы данных
DB_PASSWORD = "masterkey"  # Пароль базы данных

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Создаем объекты бота и диспетчера с хранилищем состояний
storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)

admin_ids = [8029793586, 642425664, 1857738565]

# ID пользователей для мониторинга
STAFF_IDS = {
    "wallace": 63736,
    "zlo": 7419,
    "formoza": 63763
}

# Расширенная конфигурация для разных типов событий и сотрудников
EVENT_CONFIG = {
    63736: {  # Wallace
        "entry": {
            "config_tree_id": 15220,  # для TABEL_INTERMEDIADATE
            "configs_tree_id_controller": 15012,  # для REG_EVENTS
            "configs_tree_id_resource": 15220,  # для REG_EVENTS
            "areas_id": 25376,  # для REG_EVENTS (вход)
            "identifier": 10587713,
            "inner_number_ev": 1064977,
            "subdiv_id": 49436
        },
        "exit": {
            "config_tree_id": 11583,
            "configs_tree_id_controller": 11375,
            "configs_tree_id_resource": 11583,
            "areas_id": 1,  # для REG_EVENTS (выход)
            "identifier": 10587713,
            "inner_number_ev": 1064977,
            "subdiv_id": 49436
        }
    },
    7419: {  # Zlo - ЗАМЕНИТЕ НА РЕАЛЬНЫЕ ЗНАЧЕНИЯ!
        "entry": {
            "config_tree_id": 15220,
            "configs_tree_id_controller": 15012,
            "configs_tree_id_resource": 15220,
            "areas_id": 25376,
            "identifier": 8651690,  # ЗАМЕНИТЬ!
            "inner_number_ev": 1064977,  # ЗАМЕНИТЬ!
            "subdiv_id": 49436
        },
        "exit": {
            "config_tree_id": 11583,
            "configs_tree_id_controller": 11375,
            "configs_tree_id_resource": 11583,
            "areas_id": 1,
            "identifier": 8651690,  # ЗАМЕНИТЬ!
            "inner_number_ev": 1064977,  # ЗАМЕНИТЬ!
            "subdiv_id": 49436
        }
    },
    63763: {  # Formoza - ЗАМЕНИТЕ НА РЕАЛЬНЫЕ ЗНАЧЕНИЯ!
        "entry": {
            "config_tree_id": 15220,
            "configs_tree_id_controller": 15012,
            "configs_tree_id_resource": 15220,
            "areas_id": 25376,
            "identifier": 10587706,  # ЗАМЕНИТЬ!
            "inner_number_ev": 1064977,  # ЗАМЕНИТЬ!
            "subdiv_id": 49436
        },
        "exit": {
            "config_tree_id": 11583,
            "configs_tree_id_controller": 11375,
            "configs_tree_id_resource": 11583,
            "areas_id": 1,
            "identifier": 10587706,  # ЗАМЕНИТЬ!
            "inner_number_ev": 1064977,  # ЗАМЕНИТЬ!
            "subdiv_id": 49436
        }
    }
}

# Состояния для FSM
class EventStates(StatesGroup):
    waiting_for_date = State()
    waiting_for_time = State()

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
    
    def create_event(self, staff_id: int, date_pass: str, time_pass: str, 
                     event_type: str) -> Tuple[bool, str]:
        """
        Создает событие входа или выхода в обеих таблицах БД
        
        Args:
            staff_id: ID сотрудника
            date_pass: Дата в формате 'YYYY-MM-DD'
            time_pass: Время в формате 'HH:MM:SS'
            event_type: 'entry' или 'exit'
        
        Returns:
            Tuple[bool, str]: (успешность операции, сообщение об ошибке)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Получаем конфигурацию для данного сотрудника и типа события
                config = EVENT_CONFIG[staff_id][event_type]
                
                # Определяем TYPE_PASS (1 - вход, 2 - выход)
                type_pass = 1 if event_type == 'entry' else 2
                
                timestamp = f"{date_pass} {time_pass}"
                
                # Создаем LAST_TIMESTAMP (текущее время + несколько секунд)
                last_timestamp = datetime.now() + timedelta(seconds=1)
                last_timestamp_str = last_timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                
                # 1. Вставка в TABEL_INTERMEDIADATE
                query_intermediate = """
                INSERT INTO TABEL_INTERMEDIADATE
                (STAFF_ID, DATE_PASS, TIME_PASS, TYPE_PASS, CONFIG_TREE_ID, 
                 AREAS_TREE_ID, PARTICIPATES_CALC, VIRTUAL_EVENTS, VIDEO_MARK, 
                 AVT_CAM_DBID, EVENT_IN_DAY_NUMBER)
                VALUES(?, ?, ?, ?, ?, ?, 1, 0, '', -1, NULL)
                """
                
                cursor.execute(query_intermediate, (
                    staff_id, 
                    date_pass, 
                    time_pass, 
                    type_pass, 
                    config['config_tree_id'],
                    config['areas_id']
                ))
                
                # 2. Вставка в REG_EVENTS
                query_reg_events = """
                INSERT INTO REG_EVENTS
                (INNER_NUMBER_EV, DATE_EV, TIME_EV, IDENTIFIER, 
                 CONFIGS_TREE_ID_CONTROLLER, CONFIGS_TREE_ID_RESOURCE, 
                 TYPE_PASS, CATEGORY_EV, SUBCATEGORY_EV, AREAS_ID, 
                 STAFF_ID, USER_ID, TYPE_IDENTIFIER, VIDEO_MARK, 
                 LAST_TIMESTAMP, IDENTIFIER_OWNER_TYPE, AVT_CAM_DBID, 
                 SUBDIV_ID, CONTROLLER_EVENT_ID, STATE_NUMBER, 
                 CTRL_TIME_ZONE_DATE_EV, CTRL_TIME_ZONE_TIME_EV)
                VALUES(?, ?, ?, ?, ?, ?, 1, 0, 0, ?, ?, NULL, 1, '', ?, 0, -1, ?, -1, '', NULL, NULL)
                """
                
                cursor.execute(query_reg_events, (
                    config['inner_number_ev'],
                    date_pass,
                    time_pass,
                    config['identifier'],
                    config['configs_tree_id_controller'],
                    config['configs_tree_id_resource'],
                    config['areas_id'],
                    staff_id,
                    timestamp,
                    config['subdiv_id']
                ))
                
                conn.commit()
                return True, ""
                
        except Exception as e:
            error_msg = f"Ошибка при создании события: {str(e)}"
            logging.error(error_msg)
            return False, error_msg

db_manager = DatabaseManager()

def format_intermediate_data(data: List[Tuple], staff_name: str) -> str:
    """Форматирует данные из таблицы TABEL_INTERMEDIADATE"""
    if not data:
        return f"📊 <b>Данные по {staff_name} (TABEL_INTERMEDIADATE)</b>\n\nДанных за последние 2 дня не найдено."
    
    message = f"📊 <b>Данные по {staff_name} (TABEL_INTERMEDIADATE)</b>\n\n"
    
    current_date = None
    for time_pass, date_pass, type_pass in data:
        if current_date != date_pass:
            current_date = date_pass
            message += f"📅 <b>{date_pass.strftime('%d.%m.%Y')}</b>\n"
        
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
        if current_date != date_ev:
            current_date = date_ev
            message += f"📅 <b>{date_ev.strftime('%d.%m.%Y')}</b>\n"
        
        area_type = "🟢 Вход" if areas_id == 25376 else "🔴 Выход"
        timestamp_str = ""
        if last_timestamp:
            timestamp_str = f" (TS: {last_timestamp.strftime('%H:%M:%S')})"
        
        message += f"  {time_ev.strftime('%H:%M:%S')} - {area_type}{timestamp_str}\n"
    
    return message

def create_main_keyboard():
    """Создает основную клавиатуру"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Получить данные")],
            [KeyboardButton(text="➕ Создать событие")],
            [KeyboardButton(text="ℹ️ Помощь")]
        ],
        resize_keyboard=True
    )
    return keyboard

def create_staff_keyboard():
    """Создает клавиатуру для выбора сотрудника"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=name, callback_data=f"staff_{staff_id}")]
        for name, staff_id in STAFF_IDS.items()
    ])
    return keyboard

def create_event_type_keyboard(staff_id: int):
    """Создает клавиатуру для выбора типа события"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Вход", callback_data=f"event_{staff_id}_entry")],
        [InlineKeyboardButton(text="🔴 Выход", callback_data=f"event_{staff_id}_exit")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_staff")]
    ])
    return keyboard

def create_staff_for_event_keyboard():
    """Создает клавиатуру для выбора сотрудника для создания события"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=name, callback_data=f"create_{staff_id}")]
        for name, staff_id in STAFF_IDS.items()
    ])
    return keyboard

def create_cancel_keyboard():
    """Создает клавиатуру с кнопкой отмены"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard

def create_quick_date_keyboard():
    """Создает клавиатуру с быстрым выбором даты"""
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=f"📅 Сегодня ({today.strftime('%d.%m.%Y')})")],
            [KeyboardButton(text=f"📅 Вчера ({yesterday.strftime('%d.%m.%Y')})")],
            [KeyboardButton(text="✍️ Ввести вручную")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard

def create_quick_time_keyboard():
    """Создает клавиатуру с быстрым выбором времени"""
    now = datetime.now()
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=f"🕐 Текущее время ({now.strftime('%H:%M:%S')})")],
            [KeyboardButton(text="08:00:00"), KeyboardButton(text="17:00:00")],
            [KeyboardButton(text="✍️ Ввести вручную")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    """Обработчик команды /start"""
    welcome_text = """
👋 Добро пожаловать в бот мониторинга проходов!

Этот бот поможет вам получить информацию о проходах сотрудников и создавать новые события.

Используйте кнопки меню ниже для навигации! 👇
    """
    
    await message.answer(welcome_text, reply_markup=create_main_keyboard(), parse_mode="HTML")

@dp.message(Command("data"))
@dp.message(F.text == "📊 Получить данные")
async def data_handler(message: types.Message):
    """Обработчик команды /data"""
    await message.answer(
        "👥 Выберите сотрудника для получения данных за последние 2 дня:",
        reply_markup=create_staff_keyboard()
    )

@dp.message(Command("create"))
@dp.message(F.text == "➕ Создать событие")
async def create_handler(message: types.Message):
    """Обработчик команды /create"""
    await message.answer(
        "➕ Выберите сотрудника для создания события:",
        reply_markup=create_staff_for_event_keyboard()
    )

@dp.message(Command("help"))
@dp.message(F.text == "ℹ️ Помощь")
async def help_handler(message: types.Message):
    """Обработчик команды /help"""
    help_text = """
🤖 <b>Справка по боту</b>

<b>Основные функции:</b>
📊 <b>Получить данные</b> - просмотр проходов сотрудника
➕ <b>Создать событие</b> - добавить новое событие входа/выхода
ℹ️ <b>Помощь</b> - эта справка

<b>Функции:</b>
• Получение данных из TABEL_INTERMEDIADATE
• Получение данных из REG_EVENTS
• Создание событий входа/выхода в обеих таблицах
• Отображение данных за последние 2 дня

<b>Обозначения:</b>
🟢 - Вход
🔴 - Выход
📊 - Данные из TABEL_INTERMEDIADATE
📋 - Данные из REG_EVENTS

<b>Формат ввода даты:</b> ДД.ММ.ГГГГ (например: 10.09.2025)
<b>Формат ввода времени:</b> ЧЧ:ММ:СС (например: 08:03:32)

Используйте кнопки меню для навигации! 👇
    """
    
    await message.answer(help_text, parse_mode="HTML")

@dp.callback_query(F.data.startswith("staff_"))
async def staff_callback_handler(callback_query: types.CallbackQuery):
    """Обработчик выбора сотрудника для просмотра данных"""
    user_id = callback_query.from_user.id
    if user_id in admin_ids:
        staff_id = int(callback_query.data.split("_")[1])
        staff_name = next(name for name, id in STAFF_IDS.items() if id == staff_id)
        
        await callback_query.message.edit_text("⏳ Получаю данные...")
        
        try:
            intermediate_data = db_manager.get_intermediate_data(staff_id)
            reg_events_data = db_manager.get_reg_events_data(staff_id)
            
            intermediate_message = format_intermediate_data(intermediate_data, staff_name)
            reg_events_message = format_reg_events_data(reg_events_data, staff_name)
            
            await callback_query.message.edit_text(intermediate_message, parse_mode="HTML")
            await callback_query.message.answer(reg_events_message, parse_mode="HTML")
            
        except Exception as e:
            error_message = f"❌ Ошибка при получении данных: {str(e)}"
            await callback_query.message.edit_text(error_message)
            logging.error(f"Database error: {e}")
        
        await callback_query.answer()

@dp.callback_query(F.data.startswith("create_"))
async def create_event_staff_handler(callback_query: types.CallbackQuery):
    """Обработчик выбора сотрудника для создания события"""
    user_id = callback_query.from_user.id
    if user_id in admin_ids:
        staff_id = int(callback_query.data.split("_")[1])
        staff_name = next(name for name, id in STAFF_IDS.items() if id == staff_id)
        
        await callback_query.message.edit_text(
            f"👤 Сотрудник: <b>{staff_name}</b>\n\nВыберите тип события:",
            reply_markup=create_event_type_keyboard(staff_id),
            parse_mode="HTML"
        )
        
        await callback_query.answer()

@dp.callback_query(F.data.startswith("event_"))
async def event_type_handler(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора типа события"""
    parts = callback_query.data.split("_")
    staff_id = int(parts[1])
    event_type = parts[2]  # 'entry' или 'exit'
    
    staff_name = next(name for name, id in STAFF_IDS.items() if id == staff_id)
    event_type_text = "🟢 Вход" if event_type == "entry" else "🔴 Выход"
    
    # Сохраняем данные в состояние
    await state.update_data(staff_id=staff_id, staff_name=staff_name, 
                           event_type=event_type)
    
    await callback_query.message.edit_text(
        f"👤 Сотрудник: <b>{staff_name}</b>\n"
        f"📝 Событие: {event_type_text}\n\n"
        f"Выберите дату или введите вручную в формате ДД.ММ.ГГГГ:",
        parse_mode="HTML"
    )
    
    await callback_query.message.answer(
        "Выберите дату:",
        reply_markup=create_quick_date_keyboard()
    )
    
    await state.set_state(EventStates.waiting_for_date)
    await callback_query.answer()

@dp.callback_query(F.data == "back_to_staff")
async def back_to_staff_handler(callback_query: types.CallbackQuery):
    """Возврат к выбору сотрудника"""
    await callback_query.message.edit_text(
        "➕ Выберите сотрудника для создания события:",
        reply_markup=create_staff_for_event_keyboard()
    )
    await callback_query.answer()

@dp.message(F.text == "❌ Отмена")
async def cancel_handler(message: types.Message, state: FSMContext):
    """Обработчик отмены операции"""
    await state.clear()
    await message.answer(
        "❌ Операция отменена.\n\nИспользуйте меню для выбора действия:",
        reply_markup=create_main_keyboard()
    )

@dp.message(EventStates.waiting_for_date)
async def process_date(message: types.Message, state: FSMContext):
    """Обработка ввода даты"""
    date_str = None
    date_obj = None
    
    # Обработка быстрых кнопок
    if message.text.startswith("📅 Сегодня"):
        date_obj = datetime.now()
        date_str = date_obj.strftime("%Y-%m-%d")
    elif message.text.startswith("📅 Вчера"):
        date_obj = datetime.now() - timedelta(days=1)
        date_str = date_obj.strftime("%Y-%m-%d")
    elif message.text == "✍️ Ввести вручную":
        await message.answer(
            "Введите дату в формате ДД.ММ.ГГГГ\nНапример: 10.09.2025",
            reply_markup=create_cancel_keyboard()
        )
        return
    else:
        # Парсинг введенной даты
        try:
            date_obj = datetime.strptime(message.text, "%d.%m.%Y")
            date_str = date_obj.strftime("%Y-%m-%d")
        except ValueError:
            await message.answer(
                "❌ Неверный формат даты!\n"
                "Выберите из меню или введите в формате ДД.ММ.ГГГГ\n"
                "Например: 10.09.2025"
            )
            return
    
    # Сохраняем дату
    await state.update_data(date_pass=date_str)
    
    data = await state.get_data()
    staff_name = data['staff_name']
    event_type = data['event_type']
    event_type_text = "🟢 Вход" if event_type == "entry" else "🔴 Выход"
    
    await message.answer(
        f"👤 Сотрудник: <b>{staff_name}</b>\n"
        f"📝 Событие: {event_type_text}\n"
        f"📅 Дата: <b>{date_obj.strftime('%d.%m.%Y')}</b>\n\n"
        f"Выберите время или введите вручную:",
        parse_mode="HTML",
        reply_markup=create_quick_time_keyboard()
    )
    
    await state.set_state(EventStates.waiting_for_time)

@dp.message(EventStates.waiting_for_time)
async def process_time(message: types.Message, state: FSMContext):
    """Обработка ввода времени и создание события"""
    time_str = None
    
    # Обработка быстрых кнопок
    if message.text.startswith("🕐 Текущее время"):
        time_obj = datetime.now()
        time_str = time_obj.strftime("%H:%M:%S")
    elif message.text == "✍️ Ввести вручную":
        await message.answer(
            "Введите время в формате ЧЧ:ММ:СС\nНапример: 08:03:32",
            reply_markup=create_cancel_keyboard()
        )
        return
    elif ":" in message.text and len(message.text) == 8:
        # Проверка формата времени (XX:XX:XX)
        try:
            time_obj = datetime.strptime(message.text, "%H:%M:%S")
            time_str = time_obj.strftime("%H:%M:%S")
        except ValueError:
            await message.answer(
                "❌ Неверный формат времени!\n"
                "Выберите из меню или введите в формате ЧЧ:ММ:СС\n"
                "Например: 08:03:32"
            )
            return
    else:
        await message.answer(
            "❌ Неверный формат времени!\n"
            "Выберите из меню или введите в формате ЧЧ:ММ:СС\n"
            "Например: 08:03:32"
        )
        return
    
    # Получаем все данные
    data = await state.get_data()
    staff_id = data['staff_id']
    staff_name = data['staff_name']
    event_type = data['event_type']
    date_pass = data['date_pass']
    
    # Создаем событие
    await message.answer("⏳ Создаю событие в обеих таблицах...", 
                       reply_markup=ReplyKeyboardRemove())
    
    success, error_msg = db_manager.create_event(staff_id, date_pass, time_str, event_type)
    
    if success:
        event_type_text = "🟢 Вход" if event_type == "entry" else "🔴 Выход"
        date_display = datetime.strptime(date_pass, "%Y-%m-%d").strftime("%d.%m.%Y")
        
        await message.answer(
            f"✅ <b>Событие успешно создано!</b>\n\n"
            f"📋 Данные добавлены в таблицы:\n"
            f"  • TABEL_INTERMEDIADATE\n"
            f"  • REG_EVENTS\n\n"
            f"👤 Сотрудник: {staff_name}\n"
            f"📝 Событие: {event_type_text}\n"
            f"📅 Дата: {date_display}\n"
            f"⏰ Время: {time_str}",
            parse_mode="HTML",
            reply_markup=create_main_keyboard()
        )
    else:
        await message.answer(
            f"❌ Ошибка при создании события!\n\n"
            f"Детали: {error_msg}\n\n"
            f"Попробуйте еще раз с помощью кнопки ниже.",
            reply_markup=create_main_keyboard()
        )
    
    # Очищаем состояние
    await state.clear()

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