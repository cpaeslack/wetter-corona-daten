"""module to load the config from the config-file"""
import json
import os

pwd = os.path.dirname(os.path.abspath(__file__))
CONFIG_SAVE_PATH = '{}/../config.json'.format(pwd)


def get_config() -> dict:
    """reads the config from the config.json"""

    with open(CONFIG_SAVE_PATH) as json_file:
        config = json.load(json_file)
    return config
