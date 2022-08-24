from datetime import datetime, timedelta
from decimal import Decimal
from os import getenv

import redis

from src.constants import EARLIEST_DATE
from src.db.db_interface import AbstractDBInstace

ONE_DAY = timedelta(days=1)


class RedisStackInstance(AbstractDBInstace):
    db = None
    jsonDB = None

    @staticmethod
    def self_init():
        RedisStackInstance.db = redis.from_url(getenv('REDIS_URL', 'redis://localhost:6379'))
        RedisStackInstance.jsonDB = RedisStackInstance.db.json()

    @staticmethod
    async def map_to_store():
        pass

    @staticmethod
    def get_single_rate(dt):
        date = dt.strftime("%Y-%m-%d")
        rates = RedisStackInstance.jsonDB.get(date, '$')
        if rates and len((rates)) == 1:
            return dict([a, Decimal(x)] for a, x in rates[0].items())
        else:
            return None

    @staticmethod
    async def get_historic_rates(start_at, end_at):
        the_date = start_at if start_at >= EARLIEST_DATE else EARLIEST_DATE
        results = []

        while the_date <= end_at:
            day_rates = RedisStackInstance.get_single_rate(the_date)
            if day_rates:
                results.append({
                    'date': the_date.date(),
                    'rates': day_rates
                })

            the_date += ONE_DAY
        return results

    @staticmethod
    async def get_rates(dt):
        checking_date = dt
        rates = RedisStackInstance.get_single_rate(checking_date)
        while not rates:
            checking_date = checking_date - ONE_DAY
            rates = RedisStackInstance.get_single_rate(checking_date)

        return {
            'date': checking_date.date(),
            'rates': rates
        }

    @staticmethod
    async def upsert_rates_by_time(ratesData):
        time = datetime.strptime(ratesData.attrib["time"], "%Y-%m-%d")
        rates = RedisStackInstance.jsonDB.get(ratesData.attrib["time"])

        if not rates:
            RedisStackInstance.jsonDB.set(
                time.date().strftime("%Y-%m-%d"),
                '$',
                {
                    c.attrib["currency"]: c.attrib["rate"] for c in list(ratesData)
                }
            )
