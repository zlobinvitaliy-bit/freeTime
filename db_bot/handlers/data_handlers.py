# handlers/data_handlers.py
import logging
from aiogram import types
from config import admin_ids, STAFF_IDS, OPVU_IDS, NAME_DICT
from database.db_manager import DatabaseManager
from keyboards.keyboards import create_staff_keyboard
from utils.formatters import format_intermediate_data, format_reg_events_data

db_manager = DatabaseManager()

async def data_handler(message: types.Message):
    """Обработчик команды /data"""
    await message.answer(
        "👥 Выберите сотрудника для получения данных за последние 2 дня:",
        reply_markup=create_staff_keyboard()
    )

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
        
async def staff_handler(message: types.Message):
    user_id = message.from_user.id
    if user_id in admin_ids:
        staff = db_manager.get_employees_work_status(OPVU_IDS)
        help_text = "🤖 <b>Справка по боту</b>\n<b>Статус сотрудников:</b>\n"
        
        # Добавляем статус для каждого сотрудника
        for staff_id, name in NAME_DICT.items():
            is_at_work = staff.get(staff_id, False)
            status = "🟢" if is_at_work else "🔴"
            help_text += f"{name} - {status}\n"
        
        await message.answer(help_text, parse_mode="HTML")