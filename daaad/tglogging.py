import logging

import telegram
from telegram import Bot, ParseMode

from .constants import ADMINS


class TelegramLoggingHandler(logging.Handler):
    def __init__(self, bot: Bot):
        super().__init__()
        self.bot = bot
        self.setLevel(logging.ERROR)
        self.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        )

    def emit(self, record):
        text = self.format(record)
        msg = '`{}`'.format(
            telegram.utils.helpers.escape_markdown(text, version=2)
        )
        for admin in ADMINS:
            self.bot.send_message(admin, msg, parse_mode=ParseMode.MARKDOWN_V2)
