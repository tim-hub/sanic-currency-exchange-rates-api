import fcntl
from os import getenv

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sanic import Sanic
from sanic.response import json, redirect

from src.constants import FALLBACK_LOCAL_DB_URL
from src.db.gino_db import GinoDBInstance
from src.db.redis_stack import RedisStackInstance
from src.service import RatesService
from src.utils import cors, parse_database_url

app = Sanic(__name__)

if getenv('USE_REDIS', False):
    rates_service = RatesService(RedisStackInstance)
else:
    app.config.update(
        parse_database_url(
            url=getenv("DATABASE_URL", FALLBACK_LOCAL_DB_URL)
        )
    )
    rates_service = RatesService(GinoDBInstance)

exchange_rates_history = rates_service.exchange_rates_history
to_exchange_rates = rates_service.to_exchange_rates
update_rates = rates_service.update_rates


@app.listener("before_server_start")
async def initialize_scheduler(app, loop):
    await rates_service.map_to_store()

    # Schedule exchangerate updates
    try:
        _ = open("../scheduler.lock", "w")
        fcntl.lockf(_.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

        scheduler = AsyncIOScheduler()
        scheduler.start()

        # Updates lates 90 days data
        scheduler.add_job(update_rates, "interval", hours=1)

        # Fill up database with rates
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


@app.route("/api/latest", methods=["GET", "HEAD"])
@cors()
async def exchange_rates(request):
    return await to_exchange_rates(request)


@app.route("/api/<date>", methods=["GET", "HEAD"])
@cors()
async def exchange_rates(request, date=None):
    return await to_exchange_rates(request, date)


@app.route("/api/history", methods=["GET", "HEAD"])
@cors()
async def exchange_history(request):
    return await exchange_rates_history(request)


@app.route("/latest", methods=["GET", "HEAD"])
@cors()
async def exchange_rates(request):
    return await to_exchange_rates(request)


@app.route("/<date>", methods=["GET", "HEAD"])
@cors()
async def exchange_rates(request, date=None):
    return await to_exchange_rates(request, date)


@app.route("/history", methods=["GET", "HEAD"])
@cors()
async def exchange_history(request):
    return await exchange_rates_history(request)


@app.route("/", methods=["GET"])
async def index(request):
    home = {
        "help": [
            {
                "description": "Get the latest foreign exchange rates.",
                "type": "GET",
                "url": "/api/latest"
            },
            {
                "description": "Get historical rates for any day since 1999-01-04.",
                "type": "GET",
                "url": "/api/2018-03-26"
            },
            {
                "description": "Rates are quoted against the Euro by default. Quote against a different currency by setting the base parameter in your request.",
                "type": "GET",
                "url": "/api/latest?base=USD"
            },
            {
                "description": "Request specific exchange rates by setting the symbols parameter.",
                "type": "GET",
                "url": "/api/latest?symbols=USD,GBP"
            },
            {
                "description": "Get historical rates for a time period.",
                "type": "GET",
                "url": "/api/history?start_at=2018-01-01&end_at=2018-09-01"
            },
            {
                "description": "Limit results to specific exchange rates to save bandwidth with the symbols parameter.",
                "type": "GET",
                "url": "/api/history?start_at=2018-01-01&end_at=2018-09-01&symbols=ILS,JPY"
            },
            {
                "description": "Quote the historical rates against a different currency.",
                "type": "GET",
                "url": "/api/history?start_at=2018-01-01&end_at=2018-09-01&base=USD"
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
