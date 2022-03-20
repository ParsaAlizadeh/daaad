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
from .clist import (
    Contest,
    fetch_desired_contests,
    utc, tehran
)

def send_contest(now: datetime, contest: Contest, context: CallbackContext):
    context.bot.send_message(
        chat_id=CHANNEL,
        text=contest.pretty_show(now),
        disable_web_page_preview=True
    )

def start_command(update: Update, context: CallbackContext):
    msg = [
        'سلام!',
        f'اطلاع رسانی کانتست‌ها داخل {CHANNEL} انجام میشه.'
    ]
    update.message.reply_text('\n'.join(msg))

def manual_command(update: Update, context: CallbackContext):
    if update.message.chat_id not in ADMINS:
        return
    event = update.message.text.split('\n')[1:]
    json = { key: event[i] for i, key in enumerate(['event', 'href', 'start', 'end'])}
    json['resource'] = ''
    contest = Contest(json)
    now = datetime.utcnow().astimezone(utc)
    send_contest(now, contest, context)
    update.message.reply_text("انجام شد")

def log_error(update: Update, context: CallbackContext):
    logging.error('Error Handler Called. [update="%s", error="%s"]', update, context.error)

def announce_contests(context: CallbackContext):
    context.bot.send_message(CHANNEL, 'سلام ملت!', disable_notification=True)
    now = datetime.utcnow().astimezone(utc)
    contests = fetch_desired_contests(now)
    for c in contests:
        send_contest(now, c, context)

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(message)s"
    )

    updater = Updater(TOKEN, use_context=True)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("manual", manual_command))
    dispatcher.add_error_handler(log_error)

    updater.job_queue.run_daily(
        callback=announce_contests,
        time=time(11, 0).replace(tzinfo=tehran),
        name="daily"
    )

    if DEBUG:
        logging.info("Start polling")
        updater.job_queue.run_once(
            callback=announce_contests,
            when=10,
            name="once (debug)"
        )
        updater.start_polling()
    else:
        logging.info("Start webhook")
        updater.start_webhook(
            listen='0.0.0.0',
            port=PORT,
            url_path=TOKEN,
            webhook_url=f'{WEBHOOK_URL}/{TOKEN}',
            cert=CERT_FILEPATH
        )

    updater.idle()

if __name__ == "__main__":
    main()
