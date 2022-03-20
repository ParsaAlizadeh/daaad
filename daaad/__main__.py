import logging

from datetime import datetime
from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext
)


from .constants import *
from .clist import fetch_desired_contests

def start_command(update: Update, context: CallbackContext):
    update.message.reply_text("سلام!")
    r = fetch_desired_contests(datetime.utcnow())
    logging.info(list(r))

def log_error(update: Update, context: CallbackContext):
    logging.error('Error Handler Called. [update="%s", error="%s"]', update, context.error)

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(message)s"
    )

    updater = Updater(TOKEN, use_context=True)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_error_handler(log_error)

    if DEBUG:
        logging.info("Start polling")
        updater.start_polling()

    updater.idle()

if __name__ == "__main__":
    main()
