# utils/formatters.py
from typing import List, Tuple

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