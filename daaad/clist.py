import requests
import logging
import pytz
from collections import defaultdict
from datetime import datetime, timedelta
from persiantools.jdatetime import JalaliDateTime
from persiantools import digits
from .constants import *


utc = pytz.utc
tehran = pytz.timezone('Asia/Tehran')

_ALLOWED_PATTERNS = defaultdict(list)
_ALLOWED_PATTERNS["codeforces.com"] = [""]
_ALLOWED_PATTERNS["atcoder.jp"] = ["beginner", "regular", "grand"]
_ALLOWED_PATTERNS["hsin.hr/coci"] = [""]
_ALLOWED_PATTERNS["codingcompetitions.withgoogle.com"] = [""]

_DISALLOWED_PATTERNS = defaultdict(list)
_DISALLOWED_PATTERNS["codeforces.com"] = ["unrated", "kotlin"]


def relative_date(d1: datetime, d2: datetime):
    a_day = timedelta(days=1)
    texts = [
        'امروز',
        'فردا',
        'پس فردا'
    ]
    for i, s in enumerate(texts):
        if d2.day == (d1 + i * a_day).day:
            return s
    logging.warning("Asked for more than %s relative date", len(texts)-1)
    return '?'


class Contest:
    def __init__(self, json):
        self.start = datetime.fromisoformat(json["start"]).replace(tzinfo=utc)
        self.end = datetime.fromisoformat(json["end"]).replace(tzinfo=utc)
        self.event = json["event"]
        self.resource = json["resource"]
        self.href = json["href"]

    def __str__(self):
        return f'<Contest "{self.event}" {self.start} {self.duration}>'

    def __repr__(self):
        return self.__str__()

    def is_desired(self) -> bool:
        for pat in _DISALLOWED_PATTERNS[self.resource]:
            if pat in self.event.lower():
                return False
        for pat in _ALLOWED_PATTERNS[self.resource]:
            if pat in self.event.lower():
                return True
        return False

    def pretty_show(self, now: datetime):
        loc_now = now.astimezone(tehran)
        loc_start = self.start.astimezone(tehran)
        loc_end = self.end.astimezone(tehran)

        jalali_now = JalaliDateTime.to_jalali(loc_now)
        jalali_start = JalaliDateTime.to_jalali(loc_start)
        jalali_end = JalaliDateTime.to_jalali(loc_end)

        relative = relative_date(jalali_now, jalali_start)

        jalali = jalali_start.strftime("%A %d %B", locale="fa")
        georgian = loc_start.strftime("%B %d")

        start_t = jalali_start.strftime("%H:%M", locale="fa")
        finish_t = jalali_end.strftime("%H:%M", locale="fa")

        delta = datetime(1, 1, 1) + (loc_end - loc_start)
        delta_t = '{} ساعت'.format(digits.en_to_fa(str(delta.hour)))
        if delta.minute > 0:
            delta_t += ' و {} دقیقه'.format(digits.en_to_fa(str(delta.minute)))

        lines = [
            f'{relative}',
            f'از ساعت {start_t}',
            f'به مدت {delta_t}',
            self.event,
            self.href
        ]
        return '\n'.join(lines)

def fetch_contests(now: datetime):
    headers = { "Authorization": f"ApiKey {APIKEY}" }
    params = {
        "limit": 200,
        "start__gte": now.isoformat(timespec='seconds'),
        "start__lte": (now + timedelta(days=2)).isoformat(timespec='seconds'),
        "order_by": "start",
        "duration__lte": timedelta(hours=5).seconds
    }
    response = requests.get(
        url="https://clist.by/api/v2/contest/",
        headers=headers,
        params=params
    )
    try:
        response.raise_for_status()
        return map(Contest, response.json()["objects"])
    except requests.HTTPError:
        logging.error(
            'failed to fetch contests. [params="%s", status_code="%s", response="%s"',
            params, response.status_code, response.text
        )
        return []

def fetch_desired_contests(now: datetime):
    return filter(
        Contest.is_desired,
        fetch_contests(now)
    )
