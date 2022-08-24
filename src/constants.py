from datetime import datetime

HISTORIC_RATES_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml"
LAST_90_DAYS_RATES_URL = (
    "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist-90d.xml"
)
DEFAULT_BASE_CURRENCY = 'EUR'

FALLBACK_LOCAL_DB_URL = "postgresql://localhost/exchangerates"

EARLIEST_DATE = datetime(1999, 1, 4)
