from datetime import datetime
from decimal import Decimal
from os import getenv

import ujson
from gino import Gino

from sqlalchemy.dialects.postgresql import JSONB

from src.constants import FALLBACK_LOCAL_DB_URL
from src.db.db_interface import AbstractDBInstace


class PostgresRepo(AbstractDBInstace):
    db = None
    repo = None

    @staticmethod
    def self_init():
        PostgresRepo.db = Gino()

        class RateRepo(PostgresRepo.db.Model):
            __tablename__ = "exchange_rates"

            date = PostgresRepo.db.Column(PostgresRepo.db.Date(), primary_key=True)
            rates = PostgresRepo.db.Column(JSONB())

            def __repr__(self):
                return "Rates [{}]".format(self.date)

        PostgresRepo.repo = RateRepo

    @staticmethod
    async def map_to_store():
        await PostgresRepo.db.set_bind(getenv("DATABASE_URL", FALLBACK_LOCAL_DB_URL),
                                       json_serializer=ujson.dumps,
                                       json_deserializer=ujson.loads
                                       )
        # Check that tables exist
        await PostgresRepo.db.gino.create_all()
        print('set up db')

    @staticmethod
    def get_repo():
        if (PostgresRepo.repo):
            return PostgresRepo.repo
        else:
            print("error no repo")

    @staticmethod
    async def get_historic_rates(start_at, end_at):
        exchange_rates = (
            await PostgresRepo.get_repo().query.where(PostgresRepo.get_repo().date >= start_at.date())
            .where(PostgresRepo.get_repo().date <= end_at.date())
            .order_by(PostgresRepo.get_repo().date.asc())
            .gino.all()
        )
        return map(lambda x: {'date': x.date, 'rates': x.rates}, exchange_rates)

    @staticmethod
    async def get_rates(dt):
        exchange_rates = (
            await PostgresRepo.get_repo().query.where(PostgresRepo.get_repo().date <= dt.date())
            .order_by(PostgresRepo.get_repo().date.desc())
            .gino.first()
        )
        return {
            'date': exchange_rates.date,
            'rates': exchange_rates.rates
        }

    @staticmethod
    async def upsert_rates_by_time(ratesData):
        time = datetime.strptime(ratesData.attrib["time"], "%Y-%m-%d").date()
        rates = await PostgresRepo.get_repo().get(time)
        if not rates:
            await PostgresRepo.get_repo().create(
                date=time,
                rates={
                    c.attrib["currency"]: Decimal(c.attrib["rate"]) for c in list(ratesData)
                },
            )
