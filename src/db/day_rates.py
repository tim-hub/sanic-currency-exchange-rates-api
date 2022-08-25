import datetime
from os import getenv
from typing import Optional, Dict

from pydantic import EmailStr, ConstrainedDecimal, constr

import redis
from redis_om import (
    EmbeddedJsonModel,
    JsonModel,
    Field,
    Migrator,
    get_redis_connection
)


# todo use this instead of dict in model
# class Rates(EmbeddedJsonModel):
#     EUR: Optional[Decimal]
#     USD: Optional[Decimal]
#     JPY: Optional[Decimal]
#     BGN: Optional[Decimal]
#     CZK: Optional[Decimal]
#     DKK: Optional[Decimal]
#     GBP: Optional[Decimal]
#     HUF: Optional[Decimal]
#     PLN: Optional[Decimal]
#     RON: Optional[Decimal]
#     SEK: Optional[Decimal]
#     CHF: Optional[Decimal]
#     ISK: Optional[Decimal]
#     NOK: Optional[Decimal]
#     HRK: Optional[Decimal]
#     TRY: Optional[Decimal]
#     AUD: Optional[Decimal]
#     BRL: Optional[Decimal]
#     CAD: Optional[Decimal]
#     CNY: Optional[Decimal]
#     HKD: Optional[Decimal]
#     IDR: Optional[Decimal]
#     ILS: Optional[Decimal]
#     INR: Optional[Decimal]
#     KRW: Optional[Decimal]
#     MXN: Optional[Decimal]
#     MYR: Optional[Decimal]
#     NZD: Optional[Decimal]
#     PHP: Optional[Decimal]
#     SGD: Optional[Decimal]
#     THB: Optional[Decimal]
#     ZAR: Optional[Decimal]


class DayRates(JsonModel):
    date: constr(regex=r'^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$') = Field(index=True
                                                                                    # sortable=True # this is so bad !!!
                                                                                    )
    rates: Dict


    class Meta:
        global_key_prefix = "day-rates"
        database = redis.from_url(getenv('REDIS_URL', 'redis://localhost:6379'))

