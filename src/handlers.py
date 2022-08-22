import itertools
from datetime import datetime
from decimal import Decimal

import requests
from defusedxml import ElementTree
from sanic import json

from src.constants import BASE_CURRENCY, HISTORIC_RATES_URL, LAST_90_DAYS_RATES_URL
from src.db.gino_db import GinoDBInstance


async def exchange_rates_history(request):
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

    exchange_rates = (
        await GinoDBInstance.get_repo().query.where(GinoDBInstance.get_repo().date >= start_at.date())
        .where(GinoDBInstance.get_repo().date <= end_at.date())
        .order_by(GinoDBInstance.get_repo().date.asc())
        .gino.all()
    )

    base = BASE_CURRENCY
    historic_rates = {}
    for er in exchange_rates:
        rates = er.rates

        if "base" in request.args and request.args["base"] != BASE_CURRENCY:
            base = request.args["base"][0]

            if base in rates:
                base_rate = Decimal(rates[base])
                rates = {
                    currency: Decimal(rate) / base_rate
                    for currency, rate in rates.items()
                }
                rates["EUR"] = Decimal(1) / base_rate
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

        historic_rates[er.date] = rates

    return json({"base": base, "start_at": start_at.date().isoformat(), "end_at": end_at.date().isoformat(),
                 "rates": historic_rates})


async def to_exchange_rates(request, date=None):
    if request.method == "HEAD":
        return json("")

    dt = datetime.now()
    if date:
        try:
            dt = datetime.strptime(date, "%Y-%m-%d")
        except ValueError as e:
            return json({"error": "{}".format(e)}, status=400)

        if dt < datetime(1999, 1, 4):
            return json(
                {"error": "There is no data for dates older then 1999-01-04."},
                status=400,
            )

    exchange_rates = (
        await GinoDBInstance.get_repo().query.where(GinoDBInstance.get_repo().date <= dt.date())
        .order_by(GinoDBInstance.get_repo().date.desc())
        .gino.first()
    )
    rates = exchange_rates.rates

    # Base
    base = BASE_CURRENCY

    if "base" in request.args and request.args["base"] != BASE_CURRENCY:
        base = request.args["base"][0]

        if base in rates:
            base_rate = Decimal(rates[base])
            rates = {
                currency: Decimal(rate) / base_rate for currency, rate in rates.items()
            }
            rates["EUR"] = Decimal(1) / base_rate
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
                {
                    "error": "Symbols '{}' are invalid for date {}.".format(
                        ",".join(symbols), dt.date()
                    )
                },
                status=400,
            )

    return json(
        {"base": base, "date": exchange_rates.date.strftime("%Y-%m-%d"), "rates": rates}
    )


async def update_rates(historic=False):
    r = requests.get(HISTORIC_RATES_URL if historic else LAST_90_DAYS_RATES_URL)
    envelope = ElementTree.fromstring(r.content)

    namespaces = {
        "gesmes": "http://www.gesmes.org/xml/2002-08-01",
        "eurofxref": "http://www.ecb.int/vocabulary/2002-08-01/eurofxref",
    }

    data = envelope.findall("./eurofxref:Cube/eurofxref:Cube[@time]", namespaces)
    for d in data:
        time = datetime.strptime(d.attrib["time"], "%Y-%m-%d").date()
        rates = await GinoDBInstance.get_repo().get(time)
        if not rates:
            await GinoDBInstance.get_repo().create(
                date=time,
                rates={
                    c.attrib["currency"]: Decimal(c.attrib["rate"]) for c in list(d)
                },
            )