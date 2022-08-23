from abc import ABC, abstractmethod


class AbstractDBInstace(ABC):


    @staticmethod
    @abstractmethod
    async def self_init():
        pass

    @staticmethod
    @abstractmethod
    async def map_to_store():
        pass

    @staticmethod
    @abstractmethod
    async def get_historic_rates(start_at, end_at):
        pass

    @staticmethod
    @abstractmethod
    async def get_rates(dt=None):
        pass

    @staticmethod
    @abstractmethod
    async def upsert_rates_by_time(d):
        pass
