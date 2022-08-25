from datetime import datetime, timedelta, date
from decimal import Decimal
from os import getenv

import redis
from redis.commands.search.query import Query
from redis_om import Migrator

from src.constants import EARLIEST_DATE
from src.db.day_rates import DayRates
from src.db.db_interface import AbstractDBInstace


ONE_DAY = timedelta(days=1)



class RedisOMRepo(AbstractDBInstace):
    db = None
    model = DayRates
    migrator = None
    search = None

    @staticmethod
    def self_init():
        RedisOMRepo.db = redis.from_url(getenv('REDIS_URL', 'redis://localhost:6379'))

        RedisOMRepo.search = RedisOMRepo.db.ft()

        DayRates.Meta.database = RedisOMRepo.db
        RedisOMRepo.model = DayRates


        RedisOMRepo.migrator = Migrator()



    @staticmethod
    async def map_to_store():
        RedisOMRepo.migrator.run()

    @staticmethod
    async def get_historic_rates(start_at, end_at):
        the_date = start_at if start_at >= EARLIEST_DATE else EARLIEST_DATE
        results = []

        while the_date <= end_at:
            day_rates = RedisOMRepo.model.find(DayRates.date == the_date.strftime("%Y-%m-%d"))
            if day_rates and len(day_rates.all()):
                results.append({
                    'date': the_date.date(),
                    'rates': day_rates.first().dict()['rates']
                })

            the_date += ONE_DAY
        return results

    @staticmethod
    async def get_rates(dt):
        checking_date = dt
        day_rates_query = RedisOMRepo.model.find(DayRates.date == checking_date.strftime("%Y-%m-%d"))

        while len(day_rates_query.all()) < 1:
            checking_date = checking_date - ONE_DAY
            day_rates_query = RedisOMRepo.model.find(DayRates.date == checking_date.strftime("%Y-%m-%d"))

        return {
            'date': checking_date.date(),
            'rates': day_rates_query.first().dict()['rates']
        }

    @staticmethod
    async def upsert_rates_by_time(ratesData):
        time = datetime.strptime(ratesData.attrib["time"], "%Y-%m-%d")
        rates_query = RedisOMRepo.model.find(DayRates.date == ratesData.attrib["time"])
        if len(rates_query.all()) == 0:
            new_rates = DayRates(
                date = time.date().strftime("%Y-%m-%d"),
                rates = {
                    c.attrib["currency"]: Decimal(c.attrib["rate"]) for c in list(ratesData)
                }
            )
            new_rates.save()
