import requests
import logging
import pytz
import itertools
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
_ALLOWED_PATTERNS["usaco.org"] = [""]

_DISALLOWED_PATTERNS = defaultdict(list)
_DISALLOWED_PATTERNS["codeforces.com"] = ["unrated", "kotlin"]
_DISALLOWED_PATTERNS["usaco.org"] = ["ioi"]

_DAYS = 2


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
    logging.warning(
        "asked for more than %s relative date, return '?' [from=%s, to=%s]",
        len(texts)-1, d1, d2
    )
    return '?'

def show_dt(dt: timedelta):
    days = dt.days
    total_minutes = dt.seconds // 60
    minutes = total_minutes % 60
    hours = total_minutes // 60
    result = []
    if days > 0:
        result.append(f"{days} روز")
    if hours > 0:
        result.append(f"{hours} ساعت")
    if minutes > 0:
        result.append(f"{minutes} دقیقه")
    return digits.en_to_fa(" و ".join(result))


class Contest:
    def __init__(self, json):
        self.start = datetime.fromisoformat(json["start"]).replace(tzinfo=utc)
        self.end = datetime.fromisoformat(json["end"]).replace(tzinfo=utc)
        self.event = json["event"]
        self.resource = json["resource"]
        self.href = json["href"]

    def __str__(self):
        return f'<Contest "{self.event}" {self.start}>'

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

        delta_t = show_dt(loc_end - loc_start)

        lines = [
            f'{relative}، {jalali}',
            f'از ساعت {start_t}',
            f'به مدت {delta_t}',
            self.event,
            self.href
        ]
        return '\n'.join(lines)

def fetch_contests(**params):
    headers = { "Authorization": f"ApiKey {APIKEY}" }
    result = []
    try:
        response = requests.get(
            url="https://clist.by/api/v2/contest/",
            headers=headers,
            params=params
        )
        response.raise_for_status()
        result = map(Contest, response.json()["objects"])
    except requests.ConnectionError:
        logging.exception(
            'connection error in fetch contests, return empty list [params="%s"]',
            params
        )
    except requests.HTTPError:
        logging.exception(
            'http error in fetch contests, return empty list [params="%s", status_code="%s", response="%s"]',
            params, response.status_code, response.text
        )
    return result

def fetch_general():
    now = datetime.utcnow().replace(tzinfo=utc)
    return filter(
        Contest.is_desired,
        fetch_contests(
            start__gte=now.isoformat(timespec='seconds'),
            start__lte=(now + timedelta(days=_DAYS)).isoformat(timespec='seconds'),
            duration__lte=timedelta(hours=5).seconds
        )
    )

def fetch_ioi():
    now = datetime.utcnow().replace(tzinfo=utc)
    return fetch_contests(
        start__gte=now.isoformat(timespec='seconds'),
        start__lte=(now + timedelta(days=1)).isoformat(timespec='seconds'),
        resource="stats.ioinformatics.org"
    )

def fetch_upcoming():
    return sorted(
        itertools.chain(fetch_general(), fetch_ioi()),
        key=lambda c: c.start
    )
