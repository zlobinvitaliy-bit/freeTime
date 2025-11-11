# database/manager.py
import logging
from datetime import datetime, timedelta
from typing import List, Tuple
import fdb
from config import DB_HOST, DB_PATH, DB_USER, DB_PASSWORD, EVENT_CONFIG

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
    
    def get_employees_work_status(self, staff_ids: List[int]) -> dict:
        """Возвращает словарь с состоянием сотрудников на работе {staff_id: bool}
        
        Args:
            staff_ids: Список идентификаторов сотрудников
            
        Returns:
            Словарь, где ключ - staff_id, значение - True если сотрудник на работе
            (последнее событие за сегодня с TYPE_PASS = 1)
        """
        result = {}
        today = datetime.now().date()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for staff_id in staff_ids:
                # Получаем данные для конкретного сотрудника
                two_days_ago = today - timedelta(days=2)
                
                query = """
                SELECT TIME_PASS, DATE_PASS, TYPE_PASS
                FROM TABEL_INTERMEDIADATE 
                WHERE STAFF_ID = ? 
                AND DATE_PASS >= ?
                ORDER BY DATE_PASS DESC, TIME_PASS DESC
                """
                
                cursor.execute(query, (staff_id, two_days_ago))
                records = cursor.fetchall()
                
                if not records:
                    # Если нет записей за последние 2 дня, считаем что сотрудник не на работе
                    result[staff_id] = False
                    continue
                
                # Берем самую последнюю запись (первую в результате из-за сортировки DESC)
                last_record = records[0]
                time_pass, date_pass, type_pass = last_record
                
                # Проверяем условия: сегодняшняя дата и TYPE_PASS = 1
                is_at_work = (date_pass == today and type_pass == 1)
                result[staff_id] = is_at_work
        
        return result
    
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
        """Создает событие входа или выхода в обеих таблицах БД"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                config = EVENT_CONFIG[staff_id][event_type]
                type_pass = 1 if event_type == 'entry' else 2
                timestamp = f"{date_pass} {time_pass}"
                
                last_timestamp = datetime.now() + timedelta(seconds=1)
                last_timestamp_str = last_timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                
                # Вставка в TABEL_INTERMEDIADATE
                query_intermediate = """
                INSERT INTO TABEL_INTERMEDIADATE
                (STAFF_ID, DATE_PASS, TIME_PASS, TYPE_PASS, CONFIG_TREE_ID, 
                 AREAS_TREE_ID, PARTICIPATES_CALC, VIRTUAL_EVENTS, VIDEO_MARK, 
                 AVT_CAM_DBID, EVENT_IN_DAY_NUMBER)
                VALUES(?, ?, ?, ?, ?, ?, 1, 0, '', -1, NULL)
                """
                
                cursor.execute(query_intermediate, (
                    staff_id, date_pass, time_pass, type_pass, 
                    config['config_tree_id'], 25376
                ))
                
                # Вставка в REG_EVENTS
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
                    config['inner_number_ev'], date_pass, time_pass,
                    config['identifier'], config['configs_tree_id_controller'],
                    config['configs_tree_id_resource'], config['areas_id'],
                    staff_id, timestamp, config['subdiv_id']
                ))
                
                conn.commit()
                return True, ""
                
        except Exception as e:
            error_msg = f"Ошибка при создании события: {str(e)}"
            logging.error(error_msg)
            return False, error_msg