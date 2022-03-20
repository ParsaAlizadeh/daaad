import functools
import logging

from datetime import datetime, time
from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext
)

from .constants import *
from .clist import fetch_desired_contests, utc, tehran

def start_command(update: Update, context: CallbackContext):
    msg = [
        'سلام!',
        f'اطلاع رسانی کانتست‌ها داخل {CHANNEL} انجام میشه.'
    ]
    update.message.reply_text('\n'.join(msg))

def log_error(update: Update, context: CallbackContext):
    logging.error('Error Handler Called. [update="%s", error="%s"]', update, context.error)

def announce_contests(context: CallbackContext):
    send_message = functools.partial(context.bot.send_message, CHANNEL)
    send_message('سلام ملت!')
    now = datetime.utcnow().astimezone(utc)
    events = fetch_desired_contests(now)
    for ev in events:
        send_message(ev.pretty_show(now))

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(message)s"
    )

    updater = Updater(TOKEN, use_context=True)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_error_handler(log_error)

    updater.job_queue.run_once(
        callback=announce_contests,
        when=10,
        name="announce contest"
    )

    if DEBUG:
        logging.info("Start polling")
        updater.start_polling()

    updater.idle()

if __name__ == "__main__":
    main()
