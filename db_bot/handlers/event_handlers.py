# handlers/event_handlers.py
from datetime import datetime, timedelta
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from config import admin_ids, STAFF_IDS
from database.db_manager import DatabaseManager
from keyboards.keyboards import (
    create_main_keyboard, create_staff_for_event_keyboard, 
    create_event_type_keyboard, create_quick_date_keyboard, 
    create_quick_time_keyboard, create_cancel_keyboard
)
from states.states import EventStates

db_manager = DatabaseManager()

async def create_handler(message: types.Message):
    """Обработчик команды /create"""
    await message.answer(
        "➕ Выберите сотрудника для создания события:",
        reply_markup=create_staff_for_event_keyboard()
    )

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

async def event_type_handler(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора типа события"""
    parts = callback_query.data.split("_")
    staff_id = int(parts[1])
    event_type = parts[2]
    
    staff_name = next(name for name, id in STAFF_IDS.items() if id == staff_id)
    event_type_text = "🟢 Вход" if event_type == "entry" else "🔴 Выход"
    
    await state.update_data(staff_id=staff_id, staff_name=staff_name, event_type=event_type)
    
    await callback_query.message.edit_text(
        f"👤 Сотрудник: <b>{staff_name}</b>\n"
        f"📝 Событие: {event_type_text}\n\n"
        f"Выберите дату или введите вручную в формате ДД.ММ.ГГГГ:",
        parse_mode="HTML"
    )
    
    await callback_query.message.answer("Выберите дату:", reply_markup=create_quick_date_keyboard())
    await state.set_state(EventStates.waiting_for_date)
    await callback_query.answer()

async def back_to_staff_handler(callback_query: types.CallbackQuery):
    """Возврат к выбору сотрудника"""
    await callback_query.message.edit_text(
        "➕ Выберите сотрудника для создания события:",
        reply_markup=create_staff_for_event_keyboard()
    )
    await callback_query.answer()

async def process_date(message: types.Message, state: FSMContext):
    """Обработка ввода даты"""
    date_str = None
    date_obj = None
    
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

async def process_time(message: types.Message, state: FSMContext):
    """Обработка ввода времени и создание события"""
    time_str = None
    
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
    
    data = await state.get_data()
    staff_id = data['staff_id']
    staff_name = data['staff_name']
    event_type = data['event_type']
    date_pass = data['date_pass']
    
    await message.answer("⏳ Создаю событие...", reply_markup=ReplyKeyboardRemove())
    
    status, message_text = db_manager.create_event(staff_id, date_pass, time_str, event_type)
    
    event_type_text = "🟢 Вход" if event_type == "entry" else "🔴 Выход"
    date_display = datetime.strptime(date_pass, "%Y-%m-%d").strftime("%d.%m.%Y")
    
    if status == 'success':
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
    elif status == 'queued':
        await message.answer(
            f"🟡 <b>Сервер БД недоступен. Событие в очереди.</b>\n\n"
            f"Событие будет автоматически создано, как только сервер снова будет онлайн.\n\n"
            f"👤 Сотрудник: {staff_name}\n"
            f"📝 Событие: {event_type_text}\n"
            f"📅 Дата: {date_display}\n"
            f"⏰ Время: {time_str}",
            parse_mode="HTML",
            reply_markup=create_main_keyboard()
        )
    else: # status == 'error'
        await message.answer(
            f"❌ <b>Ошибка при создании события!</b>\n\n"
            f"Детали: {message_text}\n\n"
            f"Попробуйте еще раз с помощью кнопки ниже.",
            reply_markup=create_main_keyboard(),
            parse_mode="HTML"
        )
    
    await state.clear()