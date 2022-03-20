import requests
import logging
import pytz
from collections import defaultdict
from datetime import datetime, timedelta
from .constants import *


utc = pytz.utc
tehran = pytz.timezone('Asia/Tehran')

_ALLOWED_PATTERNS = defaultdict(list)
_ALLOWED_PATTERNS["codeforces.com"] = [""]
_ALLOWED_PATTERNS["atcoder.jp"] = ["beginner", "regular", "grand"]

_DISALLOWED_PATTERNS = defaultdict(list)
_DISALLOWED_PATTERNS["codeforces.com"] = ["unrated", "kotlin"]


class Contest:
    def __init__(self, json):
        self.duration = json["duration"]
        self.start = datetime.fromisoformat(json["start"]).replace(tzinfo=utc)
        self.end = datetime.fromisoformat(json["end"]).replace(tzinfo=utc)
        self.event = json["event"]
        self.host = json["host"]
        self.href = json["href"]
        self.resource_id = json["resource_id"]

    def __str__(self):
        return f'<Contest "{self.event}" {self.start} {self.duration}>'

    def __repr__(self):
        return self.__str__()

    def is_desired(self) -> bool:
        for pat in _DISALLOWED_PATTERNS[self.host]:
            if pat in self.event.lower():
                return False
        for pat in _ALLOWED_PATTERNS[self.host]:
            if pat in self.event.lower():
                return True
        return False


def fetch_contests(now: datetime):
    now = now.replace(microsecond=0)
    headers = { "Authorization": f"ApiKey {APIKEY}" }
    params = {
        "limit": 200,
        "start__gte": now.isoformat(),
        "start__lte": (now + timedelta(days=3)).isoformat(),
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
    return list(filter(
        Contest.is_desired,
        fetch_contests(now)
    ))