# keyboards/keyboards.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from config import STAFF_IDS
from datetime import datetime, timedelta

def create_main_keyboard():
    """Создает основную клавиатуру"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Получить данные")],
            [KeyboardButton(text="➕ Создать событие")],
            [KeyboardButton(text="⭐ ОПВУ")]
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

def create_events_for_edit_keyboard(events):
    """Создает инлайн-клавиатуру для выбора события для редактирования.

    Args:
        events: Список событий, полученный из db_manager.get_last_four_events().

    Returns:
        Объект InlineKeyboardMarkup с кнопками для каждого события.
    """
    buttons = []
    for event in events:
        # Распаковываем данные о событии
        db_key, staff_id, date_pass, time_pass, type_pass = event
        # Определяем иконку и имя сотрудника
        event_type_text = "🟢" if type_pass == 1 else "🔴"
        staff_name = next((name for name, s_id in STAFF_IDS.items() if s_id == staff_id), "Unknown")
        
        # Формируем текст для кнопки
        button_text = f"{event_type_text} {staff_name} - {date_pass.strftime('%d.%m')} {time_pass.strftime('%H:%M:%S')}"
        # Создаем callback_data, содержащий уникальный ключ события (db_key)
        callback_data = f"edit_event_{db_key.decode('utf-8')}"
        buttons.append([InlineKeyboardButton(text=button_text, callback_data=callback_data)])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)