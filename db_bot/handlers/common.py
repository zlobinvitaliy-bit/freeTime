# handlers/common.py
from aiogram import types
from aiogram.fsm.context import FSMContext
from keyboards.keyboards import create_main_keyboard, create_cancel_keyboard

async def start_handler(message: types.Message):
    """Обработчик команды /start"""
    welcome_text = """
👋 Добро пожаловать в бот мониторинга проходов!

Этот бот поможет вам получить информацию о проходах сотрудников и создавать новые события.

Используйте кнопки меню ниже для навигации! 👇
    """
    
    await message.answer(welcome_text, reply_markup=create_main_keyboard(), parse_mode="HTML")

async def cancel_handler(message: types.Message, state: FSMContext):
    """Обработчик отмены операции"""
    await state.clear()
    await message.answer(
        "❌ Операция отменена.\n\nИспользуйте меню для выбора действия:",
        reply_markup=create_main_keyboard()
    )