# sysadmin_bot/config_loader.py

from .config import TELEGRAM_BOT_TOKEN, OWNER_ID, MACHINE_PASSWORD

def get_telegram_bot_token():
    return TELEGRAM_BOT_TOKEN

def get_owner_id():
    return OWNER_ID

def get_machine_password():
    return MACHINE_PASSWORD
