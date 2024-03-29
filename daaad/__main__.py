import functools
import logging

from datetime import datetime, time, timedelta
from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    JobQueue
)

from .constants import *
from .clist import (
    Contest,
    fetch_upcoming,
    utc, tehran
)
from .tglogging import TelegramLoggingHandler


root_logger = logging.getLogger()


def log_error(update: Update, context: CallbackContext):
    logging.error('error handler called. [update="%s", error="%s"]', update, context.error)

def start_command(update: Update, context: CallbackContext):
    msg = [
        'سلام!',
        f'اطلاع رسانی کانتست‌ها داخل {CHANNEL} انجام میشه.'
    ]
    update.message.reply_text('\n'.join(msg))

def manual_command(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if chat_id not in ADMINS:
        logging.info("illegal use of manual [chat_id=%s]", chat_id)
        return
    event = update.message.text.split('\n')[1:]
    json = { key: event[i] for i, key in enumerate(['event', 'href', 'start', 'end'])}
    json['resource'] = ''
    contest = Contest(json)
    announce_contest(contest, context)

    update.message.reply_text("انجام شد")
    logging.info("manual announce done [chat_id=%s, contest=%s]", chat_id, contest)

def announce_contest(contest: Contest, context: CallbackContext):
    now = datetime.utcnow().replace(tzinfo=utc)
    msg = context.bot.send_message(
        chat_id=CHANNEL,
        text=contest.pretty_show(now),
        disable_web_page_preview=True
    )
    set_alarm(now, contest, context.job_queue, msg.message_id)

def announce_alarm(context: CallbackContext):
    job = context.job
    message_id = job.context["message_id"]
    contest = job.context["contest"]
    text = ['یک ساعت مونده', contest.event, contest.href]
    context.bot.send_message(
        chat_id=CHANNEL,
        text='\n'.join(text),
        reply_to_message_id=message_id,
        disable_web_page_preview=True
    )

def set_alarm(now: datetime, contest: Contest, job_queue: JobQueue, message_id=None):
    if contest.resource == 'stats.ioinformatics.org':
        return
    alarm_time = contest.start - timedelta(hours=1)
    previous_jobs = job_queue.get_jobs_by_name(contest.event)
    for job in previous_jobs:
        job.schedule_removal()
    if alarm_time > now:
        logging.info('set contest alarm [contest=%s, alarm_time=%s]', contest, alarm_time)
        job_queue.run_once(
            callback=announce_alarm,
            when=alarm_time,
            name=contest.event,
            context={
                "message_id": message_id,
                "contest": contest
            }
        )

def daily_procedure(context: CallbackContext):
    upcoming = fetch_upcoming()
    if not upcoming:
        logging.info("no contest found today")
        return
    logging.info("start daily announce [contests=%s]", upcoming)
    for contest in upcoming:
        announce_contest(contest, context)

def initial_procedure(context: CallbackContext):
    logging.info('initializing alarms')
    now = datetime.utcnow().replace(tzinfo=utc)
    upcoming = fetch_upcoming()
    for contest in upcoming:
        set_alarm(now, contest, context.job_queue)

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    updater = Updater(TOKEN, use_context=True)

    tglogging = TelegramLoggingHandler(updater.bot)
    root_logger.addHandler(tglogging)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("manual", manual_command))
    dispatcher.add_error_handler(log_error)

    updater.job_queue.run_daily(
        callback=daily_procedure,
        time=time(11, 0).replace(tzinfo=tehran),
        name="daily procedure"
    )

    updater.job_queue.run_once(
        callback=initial_procedure,
        when=5,
        name="initial procedure"
    )

    if DEBUG:
        logging.info("start polling")
        updater.job_queue.run_once(
            callback=daily_procedure,
            when=5,
            name="once (debug)"
        )
        updater.start_polling()
    else:
        logging.info(
            "start webhook [webhook_url=%s, port=%s]",
            WEBHOOK_URL, PORT
        )
        updater.start_webhook(
            listen='0.0.0.0',
            port=PORT,
            url_path=TOKEN,
            webhook_url=f'{WEBHOOK_URL}/{TOKEN}',
        )

    updater.idle()

if __name__ == "__main__":
    main()
