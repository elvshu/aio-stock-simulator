import datetime

import pytz

INDUSTRY_TIMEZONE = pytz.timezone("Australia/Melbourne")


def as_industry_time(time_: datetime.datetime) -> datetime.datetime:
    return time_.astimezone(INDUSTRY_TIMEZONE)


def industry_midnight(time_: datetime.datetime) -> datetime.datetime:
    industry_time = as_industry_time(time_)
    return industry_time.replace(hour=0, minute=0, second=0, microsecond=0)
