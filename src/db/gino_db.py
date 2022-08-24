from datetime import datetime
from decimal import Decimal
from os import getenv

import ujson
from gino import Gino

from sqlalchemy.dialects.postgresql import JSONB

from src.constants import FALLBACK_LOCAL_DB_URL
from src.db.db_interface import AbstractDBInstace


class GinoDBInstance(AbstractDBInstace):
    db = None
    repo = None

    @staticmethod
    def self_init():
        GinoDBInstance.db = Gino()

        class RateRepo(GinoDBInstance.db.Model):
            __tablename__ = "exchange_rates"

            date = GinoDBInstance.db.Column(GinoDBInstance.db.Date(), primary_key=True)
            rates = GinoDBInstance.db.Column(JSONB())

            def __repr__(self):
                return "Rates [{}]".format(self.date)

        GinoDBInstance.repo = RateRepo

    @staticmethod
    async def map_to_store():
        await GinoDBInstance.db.set_bind(getenv("DATABASE_URL", FALLBACK_LOCAL_DB_URL),
                                         json_serializer=ujson.dumps,
                                         json_deserializer=ujson.loads
                                         )
        # Check that tables exist
        await GinoDBInstance.db.gino.create_all()
        print('set up db')

    @staticmethod
    def get_repo():
        if (GinoDBInstance.repo):
            return GinoDBInstance.repo
        else:
            print("error no repo")

    @staticmethod
    async def get_historic_rates(start_at, end_at):
        exchange_rates = (
            await GinoDBInstance.get_repo().query.where(GinoDBInstance.get_repo().date >= start_at.date())
            .where(GinoDBInstance.get_repo().date <= end_at.date())
            .order_by(GinoDBInstance.get_repo().date.asc())
            .gino.all()
        )
        return map(lambda x: {'date': x.date, 'rates': x.rates}, exchange_rates)

    @staticmethod
    async def get_rates(dt):
        exchange_rates = (
            await GinoDBInstance.get_repo().query.where(GinoDBInstance.get_repo().date <= dt.date())
            .order_by(GinoDBInstance.get_repo().date.desc())
            .gino.first()
        )
        return {
            'date': exchange_rates.date,
            'rates': exchange_rates.rates
        }

    @staticmethod
    async def upsert_rates_by_time(ratesData):
        time = datetime.strptime(ratesData.attrib["time"], "%Y-%m-%d").date()
        rates = await GinoDBInstance.get_repo().get(time)
        if not rates:
            await GinoDBInstance.get_repo().create(
                date=time,
                rates={
                    c.attrib["currency"]: Decimal(c.attrib["rate"]) for c in list(ratesData)
                },
            )
