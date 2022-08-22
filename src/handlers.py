import itertools
from datetime import datetime
from decimal import Decimal

import requests
from sanic import json

from src.constants import BASE_CURRENCY, HISTORIC_RATES_URL, LAST_90_DAYS_RATES_URL


async def exchange_rates_history(request, rateModel):
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
        await rateModel.query.where(rateModel.date >= start_at.date())
        .where(rateModel.date <= end_at.date())
        .order_by(rateModel.date.asc())
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


async def to_exchange_rates(request, rateModel, date=None):
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
        await rateModel.query.where(rateModel.date <= dt.date())
        .order_by(rateModel.date.desc())
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
