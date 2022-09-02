"""module to load the config"""
import os
from dotenv import load_dotenv

pwd = os.path.dirname(os.path.abspath(__file__))
CONFIG_SAVE_PATH = '{}/../config.json'.format(pwd)


def get_config() -> dict:

    load_dotenv()
    config = {
        "general": {
            "sampling_time": int(os.getenv("SAMPLING_TIME"))
           },
        "openweatherapi": {
            "api_key": os.getenv("API_KEY")
            },
        "influxdb": {
            "username": os.getenv("DB_USERNAME"),
            "password": os.getenv("DB_PASSWORD"),
            "host": os.getenv("DB_HOST"),
            "dbname": os.getenv("DB_NAME"),
            "port": os.getenv("DB_PORT"),
            "table_weather": os.getenv("DB_TABLE_WEATHER"),
            "table_rki": os.getenv("DB_TABLE_RKI")
            }
        }

    return config
