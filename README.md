# Sanic Current Exchange Rate Api

This is a self hosted, free, currency rate api, free demo at [exchange-rate.bai.uno](https://exchange-rate.bai.uno).

The current and historical foreign exchange rates data are from [European Central Bank](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html).

## Usage

#### Lates & specific date rates
Get the latest foreign exchange rates.

```http
GET /latest
```

Get historical rates for any day since 1999.

```http
GET /2018-03-26
```

Rates are quoted against the Euro by default. Quote against a different currency by setting the base parameter in your request.

```http
GET /latest?base=USD
```

Request specific exchange rates by setting the symbols parameter.

```http
GET /latest?symbols=USD,GBP
```

#### Rates history
Get historical rates for a time period.

```http
GET /history?start_at=2018-01-01&end_at=2018-09-01
```

Limit results to specific exchange rates to save bandwidth with the symbols parameter.

```http
GET /history?start_at=2018-01-01&end_at=2018-09-01&symbols=ILS,JPY
```

Quote the historical rates against a different currency.

```http
GET /history?start_at=2018-01-01&end_at=2018-09-01&base=USD
```

#### Client side usage

The primary use case is client side. For instance, with [money.js](https://openexchangerates.github.io/money.js/) in the browser

```js
let demo = () => {
  let rate = fx(1).from("GBP").to("USD")
  alert("£1 = $" + rate.toFixed(4))
}

fetch('https://api.exchangeratesapi.io/latest')
  .then((resp) => resp.json())
  .then((data) => fx.rates = data.rates)
  .then(demo)
```

# Why a new frok
This project is a fork from [ExchangeRatesApi project](https://github.com/exchangeratesapi/exchangeratesapi/), the original project is great,
 but as a project, is seems like they have some outdated dependencies and hard to deploy.
 
 - sanic at original project is old, 0.8.x
 - no specific version for packages
 - hard to deploy, (easy to deploy to heroku but not other platform)

## Contributing


## License
MIT