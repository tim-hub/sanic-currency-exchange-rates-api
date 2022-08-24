import itertools
from datetime import datetime
from decimal import Decimal

import requests
from defusedxml import ElementTree
from sanic import json

from src.constants import DEFAULT_BASE_CURRENCY, HISTORIC_RATES_URL, LAST_90_DAYS_RATES_URL, EARLIEST_DATE

'''
This service logic require refactoring
'''


class RatesService:

    def __init__(self, db_instance):
        self.db_instance = db_instance
        self.db_instance.self_init()

    async def map_to_store(self):
        await self.db_instance.map_to_store()

    async def exchange_rates_history(self, request):
        if request.method == "HEAD":
            return json("")

        if "start_at" in request.args and len(request.args["start_at"]) > 0:
            try:
                start_at = datetime.strptime(request.args["start_at"][0], "%Y-%m-%d")
            except ValueError as e:
                return json(
                    {"error": "start_at parameter format", "exception": "{}".format(e)},
                    status=400,
                )
        else:
            return json({"error": "missing start_at parameter"})

        if "end_at" in request.args and len(request.args["end_at"]) > 0:
            try:
                end_at = datetime.strptime(request.args["end_at"][0], "%Y-%m-%d")
            except ValueError as e:
                return json(
                    {"error": "end_at parameter format", "exception": "{}".format(e)},
                    status=400,
                )
        else:
            return json({"error": "missing end_at parameter"})

        exchange_rates = await self.db_instance.get_historic_rates(start_at, end_at)

        base = DEFAULT_BASE_CURRENCY
        historic_rates = {}
        for er in exchange_rates:
            rates = er['rates']

            if "base" in request.args and request.args["base"][0] != DEFAULT_BASE_CURRENCY:
                base = request.args["base"][0]

                if base in rates:
                    base_rate = Decimal(rates[base])
                    rates = {
                        currency: Decimal(rate) / base_rate
                        for currency, rate in rates.items()
                    }
                    rates[DEFAULT_BASE_CURRENCY] = Decimal(1) / base_rate
                else:
                    return json(
                        {"error": "Base '{}' is not supported.".format(base)}, status=400
                    )

            # Symbols
            if "symbols" in request.args:
                symbols = list(
                    itertools.chain.from_iterable(
                        [symbol.split(",") for symbol in request.args["symbols"]]
                    )
                )

                if all(symbol in rates for symbol in symbols):
                    rates = {symbol: rates[symbol] for symbol in symbols}
                else:
                    return json(
                        {"error": "Symbols '{}' are invalid.".format(",".join(symbols))},
                        status=400,
                    )

            historic_rates[er['date']] = rates

        return json({"base": base, "start_at": start_at.date().isoformat(), "end_at": end_at.date().isoformat(),
                     "rates": historic_rates})

    async def to_exchange_rates(self, request, date=None):
        if request.method == "HEAD":
            return json("")

        # date pre check
        checking_date = datetime.utcnow()
        if date:
            try:
                checking_date = datetime.strptime(date, "%Y-%m-%d")
            except ValueError as e:
                return json({"error": "{}".format(e)}, status=400)

            if checking_date < EARLIEST_DATE:
                return json(
                    {"error": "There is no data for dates older then 1999-01-04."},
                    status=400,
                )

        # base pre check
        if "base" not in request.args or len(request.args["base"]) == 0:
            base_currency = DEFAULT_BASE_CURRENCY

        elif len(request.args["base"]) == 1:
            base_currency = request.args["base"][0]
        else:
            return json(
                {"error": "Only One Base Currency is not supported."}, status=400
            )

        exchange_rates = await self.db_instance.get_rates(checking_date)
        rates = exchange_rates['rates']

        # base post check
        if base_currency != DEFAULT_BASE_CURRENCY and base_currency not in rates:
            return json(
                {"error": "Base '{}' is not supported.".format(base_currency)}, status=400
            )

        elif (base_currency != DEFAULT_BASE_CURRENCY and base_currency in rates):
            base_rate = Decimal(rates[base_currency])
            rates = {
                currency: Decimal(rate) / base_rate for currency, rate in rates.items()
            }
            rates[DEFAULT_BASE_CURRENCY] = Decimal(1) / base_rate

        # else
        # base currency is default currency

        # symbols post validation
        if "symbols" in request.args:
            symbols = list(
                itertools.chain.from_iterable(
                    [symbol.split(",") for symbol in request.args["symbols"]]
                )
            )

            if all(symbol in rates for symbol in symbols):
                rates = {symbol: rates[symbol] for symbol in symbols}
            else:
                return json(
                    {
                        "error": "Symbols '{}' are invalid for date {}.".format(
                            ",".join(symbols), checking_date.date()
                        )
                    },
                    status=400,
                )

        return json(
            {"base": base_currency, "date": exchange_rates['date'].strftime("%Y-%m-%d"), "rates": rates}
        )

    async def update_rates(self, historic=False):
        r = requests.get(HISTORIC_RATES_URL if historic else LAST_90_DAYS_RATES_URL)
        envelope = ElementTree.fromstring(r.content)

        namespaces = {
            "gesmes": "http://www.gesmes.org/xml/2002-08-01",
            "eurofxref": "http://www.ecb.int/vocabulary/2002-08-01/eurofxref",
        }

        data = envelope.findall("./eurofxref:Cube/eurofxref:Cube[@time]", namespaces)

        for d in data:
            await self.db_instance.upsert_rates_by_time(d)
