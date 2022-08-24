# How to run locally
- [Redis Stack Store](README.md)


Make sure docker is installed.

- `git clone https://github.com/tim-hub/sanic-currency-exchange-rates-api`


## local dev

0. python 3.10
0. export DATABASE_URL = 'psql url'
1. poetry install
2. poetry run python src/main.py 


## docker

```
docker build -t rate-api . && docker run --name rate-api -t -i -e DATABASE_URL=postgresql://user:pwd@dburl/exchange rate-api 
```

# todo Refactor and Improvement

- [ ] unit test
- [x] integration test 