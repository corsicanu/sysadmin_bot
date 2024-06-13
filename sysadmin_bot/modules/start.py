# sysadmin_bot/modules/start.py

import logging
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler
from ..config_loader import get_owner_id

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

OWNER_ID = get_owner_id()

def is_owner(update: Update) -> bool:
    return update.message.from_user.id == int(OWNER_ID)

def start(update: Update, context: CallbackContext) -> None:
    if not is_owner(update):
        update.message.reply_text('GTFO haha')
        logger.info(f'Ignoring command from non-owner user {update.effective_user.id}')
        return
    update.message.reply_text('Welcome to sysadmin bot!')

def register_handlers(dp):
    dp.add_handler(CommandHandler("start", start, run_async=True))
