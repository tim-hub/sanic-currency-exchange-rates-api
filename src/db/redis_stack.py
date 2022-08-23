from src.db.db_interface import AbstractDBInstace


class RedisStackInstance(AbstractDBInstace):

    @staticmethod
    async def self_init():
        pass

    @staticmethod
    async def map_to_store():
        pass

    @staticmethod
    async def get_historic_rates(start_at, end_at):
        pass

    @staticmethod
    async def get_rates(dt=None):
        pass

    @staticmethod
    async def upsert_rates_by_time(d):
        pass