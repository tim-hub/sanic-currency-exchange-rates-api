from os import getenv

import ujson
from gino import Gino
from sanic import app
from sqlalchemy.dialects.postgresql import JSONB

from src.constants import FALLBACK_LOCAL_DB_URL
from src.decorators import singleton
from src.utils import parse_database_url


# @singleton
class GinoDBInstance:
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
    async def self_bind():
        await GinoDBInstance.db.set_bind(getenv("DATABASE_URL", FALLBACK_LOCAL_DB_URL),
                                         json_serializer=ujson.dumps,
                                         json_deserializer=ujson.loads
                                         )
        # # Check that tables exist
        await GinoDBInstance.db.gino.create_all()
        print('set up db')



    @staticmethod
    def get_db():
        if (GinoDBInstance.db):
            return GinoDBInstance.db
        else:
            GinoDBInstance.db = Gino()


    @staticmethod
    def get_repo():
        if (GinoDBInstance.repo):
            return GinoDBInstance.repo
        else:
            print("error no repo")



