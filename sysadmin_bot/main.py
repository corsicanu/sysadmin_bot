# sysadmin_bot/main.py

import os
import importlib
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.ext import CallbackContext
from .config_loader import get_telegram_bot_token, get_owner_id
from .config import ALLOWED_GROUP_IDS
from . import cron

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def is_owner(update):
    return str(update.effective_user.id) == get_owner_id()

def load_modules():
    module_dir = os.path.join(os.path.dirname(__file__), 'modules')
    modules = []
    for filename in os.listdir(module_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            module_name = f'sysadmin_bot.modules.{filename[:-3]}'
            module = importlib.import_module(module_name)
            modules.append(module)
    return modules

def verify_group(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    if chat_id not in ALLOWED_GROUP_IDS:
        logger.info(f'Bot added to unauthorized group {chat_id}, leaving...')
        context.bot.leave_chat(chat_id)

def main():
    logger.info('Starting Sysadmin Bot...')
    token = get_telegram_bot_token()
    updater_instance = Updater(token, use_context=True)
    dp = updater_instance.dispatcher
    
    modules = load_modules()
    loaded_modules = [module.__name__ for module in modules]
    logger.info(f'Loaded modules: {loaded_modules}')
    
    for module in modules:
        if hasattr(module, 'register_handlers'):
            module.register_handlers(dp)
    
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, verify_group))

    updater_instance.start_polling()
    logger.info('Sysadmin Bot started. Listening for commands...')
    
    cron.start_scheduler()
    updater_instance.idle()

if __name__ == '__main__':
    main()
