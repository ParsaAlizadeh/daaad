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
    announce_one(contest, context)

    update.message.reply_text("انجام شد")
    logging.info("manual announce done [chat_id=%s, contest=%s]", chat_id, contest)

def announce_daily(context: CallbackContext):
    upcoming = fetch_upcoming()
    if not upcoming:
        logging.info("no contest found today")
        return
    context.bot.send_message(CHANNEL, 'سلام ملت!', disable_notification=True)
    for contest in upcoming:
        announce_one(contest, context)

def announce_one(contest: Contest, context: CallbackContext):
    now = datetime.utcnow().astimezone(utc)
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
    alarm_time = contest.start - timedelta(hours=1)
    previous_jobs = job_queue.get_jobs_by_name(contest.event)
    if not previous_jobs and alarm_time > now:
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

def init_alarms(job_queue: JobQueue):
    logging.info('initializing alarms')
    now = datetime.utcnow().astimezone(utc)
    upcoming = fetch_upcoming()
    for contest in upcoming:
        set_alarm(now, contest, job_queue)

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
        callback=announce_daily,
        time=time(11, 0).replace(tzinfo=tehran),
        name="daily"
    )

    init_alarms(updater.job_queue)

    if DEBUG:
        logging.info("start polling")
        updater.job_queue.run_once(
            callback=announce_daily,
            when=5,
            name="once (debug)"
        )
        updater.start_polling()
    else:
        logging.info(
            "start webhook [webhook_url=%s, port=%s, cert_filepath=%s]",
            WEBHOOK_URL, PORT, CERT_FILEPATH
        )
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
