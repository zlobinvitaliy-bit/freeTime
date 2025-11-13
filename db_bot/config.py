# config.py
from datetime import datetime, timedelta

# Настройки бота
BOT_TOKEN = "7560155105:AAFPrs5kQukH9Y-IaEgPnimkGSe9vD0v5-U"

# Настройки базы данных
DB_HOST = "127.0.0.1"
DB_PATH = "T:\\PERCO.FDB"
DB_USER = "SYSDBA"
DB_PASSWORD = masterkey

# Права доступа
admin_ids = [8029793586, 642425664, 1857738565]

# Сотрудники
STAFF_IDS = {
    "wallace": 63736,
    "zlo": 7419,
    "formoza": 63763
}

OPVU_IDS = [29734, 7339, 29413, 61109, 51051, 62426, 30059, 29798, 28018]

NAME_DICT = {
    29734: "Женек",         
    7339:  "Шапыч",          
    30059: "Санек",         
    29413: "Андрей",        
    61109: "Брусов",        
    51051: "Серега",        
    62426: "Максим",        
    29798: "Артем Д",     
    28018: "Артем П"
}

# Конфигурация событий
EVENT_CONFIG = {
    63736: {
        "entry": {
            "config_tree_id": 15220,
            "configs_tree_id_controller": 15012,
            "configs_tree_id_resource": 15220,
            "areas_id": 25376,
            "identifier": 10587713,
            "inner_number_ev": 1064977,
            "subdiv_id": 49436
        },
        "exit": {
            "config_tree_id": 11583,
            "configs_tree_id_controller": 11375,
            "configs_tree_id_resource": 11583,
            "areas_id": 1,
            "identifier": 10587713,
            "inner_number_ev": 1064977,
            "subdiv_id": 49436
        }
    },
    7419: {
        "entry": {
            "config_tree_id": 15220,
            "configs_tree_id_controller": 15012,
            "configs_tree_id_resource": 15220,
            "areas_id": 25376,
            "identifier": 8651690,
            "inner_number_ev": 1064977,
            "subdiv_id": 49436
        },
        "exit": {
            "config_tree_id": 11583,
            "configs_tree_id_controller": 11375,
            "configs_tree_id_resource": 11583,
            "areas_id": 1,
            "identifier": 8651690,
            "inner_number_ev": 1064977,
            "subdiv_id": 49436
        }
    },
    63763: {
        "entry": {
            "config_tree_id": 15220,
            "configs_tree_id_controller": 15012,
            "configs_tree_id_resource": 15220,
            "areas_id": 25376,
            "identifier": 10587706,
            "inner_number_ev": 1064977,
            "subdiv_id": 49436
        },
        "exit": {
            "config_tree_id": 11583,
            "configs_tree_id_controller": 11375,
            "configs_tree_id_resource": 11583,
            "areas_id": 1,
            "identifier": 10587706,
            "inner_number_ev": 1064977,
            "subdiv_id": 49436
        }
    }
}