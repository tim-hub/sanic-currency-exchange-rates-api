import fcntl
from datetime import datetime
from decimal import Decimal
from os import getenv
import defusedxml.ElementTree as ElementTree

import requests
import ujson
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sanic import Sanic
from sanic.response import json, redirect
from sqlalchemy.dialects.postgresql import JSONB

from constants import HISTORIC_RATES_URL, LAST_90_DAYS_RATES_URL
from handlers import exchange_rates_history, to_exchange_rates
from utils import parse_database_url, cors

app = Sanic(__name__)

app.config.update(
    parse_database_url(
        url=getenv("DATABASE_URL", "postgresql://localhost/exchangerates")
    )
)

# Database
from gino import Gino

db = Gino()


class RateModel(db.Model):
    __tablename__ = "exchange_rates"

    date = db.Column(db.Date(), primary_key=True)
    rates = db.Column(JSONB())

    def __repr__(self):
        return "Rates [{}]".format(self.date)


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
        rates = await RateModel.get(time)
        if not rates:
            await RateModel.create(
                date=time,
                rates={
                    c.attrib["currency"]: Decimal(c.attrib["rate"]) for c in list(d)
                },
            )


@app.listener("before_server_start")
async def initialize_scheduler(app, loop):
    await db.set_bind(getenv("DATABASE_URL", "postgresql://localhost/exchangerates"),
                      json_serializer=ujson.dumps,
                      json_deserializer=ujson.loads
                      )
    # # Check that tables exist
    await db.gino.create_all()
    print('set up db')
    # Schedule exchangerate updates
    try:
        _ = open("../scheduler.lock", "w")
        fcntl.lockf(_.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

        scheduler = AsyncIOScheduler()
        scheduler.start()

        # Updates lates 90 days data
        scheduler.add_job(update_rates, "interval", hours=1)

        # Fill up database with rates
        count = await db.func.count(RateModel.date).gino.scalar()
        scheduler.add_job(update_rates, kwargs={"historic": True})
        print('set up scheduler for fetch rates')
    except BlockingIOError:
        pass


@app.middleware("request")
async def force_ssl(request):
    if request.headers.get("X-Forwarded-Proto") == "http":
        return redirect(request.url.replace("http://", "https://", 1), status=301)


@app.middleware("request")
async def force_naked_domain(request):
    if request.host.startswith("www."):
        return redirect(request.url.replace("www.", "", 1), status=301)


@app.route("/latest", methods=["GET", "HEAD"])
@cors()
async def exchange_rates(request, date=None):
    return await to_exchange_rates(request, RateModel, date)


@app.route("/<date>", methods=["GET", "HEAD"])
@cors()
async def exchange_rates(request, date=None):
    return await to_exchange_rates(request, RateModel, date)


@app.route("/api/latest", methods=["GET", "HEAD"])
@cors()
async def exchange_rates(request, date=None):
    return await to_exchange_rates(request, RateModel, date)


@app.route("/api/<date>", methods=["GET", "HEAD"])
@cors()
async def exchange_rates(request, date=None):
    return await to_exchange_rates(request, RateModel, date)


@app.route("/history", methods=["GET", "HEAD"])
@cors()
async def exchange_history(request):
    return await exchange_rates_history(request, RateModel)


@app.route("/api/history", methods=["GET", "HEAD"])
@cors()
async def exchange_history(request):
    return await exchange_rates_history(request, RateModel)


# api.ExchangeratesAPI.io
@app.route("/", methods=["GET"])
async def index(request):
    home = {
        "help": [
            {
                "description": "Get the latest foreign exchange rates.",
                "type": "GET",
                "url": "/latest"
            },
            {
                "description": "Get historical rates for any day since 1999-01-04.",
                "type": "GET",
                "url": "/2018-03-26"
            },
            {
                "description": "Rates are quoted against the Euro by default. Quote against a different currency by setting the base parameter in your request.",
                "type": "GET",
                "url": "/latest?base=USD"
            },
            {
                "description": "Request specific exchange rates by setting the symbols parameter.",
                "type": "GET",
                "url": "/latest?symbols=USD,GBP"
            },
            {
                "description": "Get historical rates for a time period.",
                "type": "GET",
                "url": "/history?start_at=2018-01-01&end_at=2018-09-01"
            },
            {
                "description": "Limit results to specific exchange rates to save bandwidth with the symbols parameter.",
                "type": "GET",
                "url": "/history?start_at=2018-01-01&end_at=2018-09-01&symbols=ILS,JPY"
            },
            {
                "description": "Quote the historical rates against a different currency.",
                "type": "GET",
                "url": "/history?start_at=2018-01-01&end_at=2018-09-01&base=USD"
            }
        ],

        "git_repo": "https://github.com/tim-hub/sanic-currency-exchange-rates-api"
    }

    return json(home, escape_forward_slashes=False)


# Static content
app.static("/static", "./static")
app.static("/robots.txt", "./static/robots.txt")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, workers=2)
