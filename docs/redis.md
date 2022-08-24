# Migrate Sanic Currency Exchange Rates Api to Use Redis Stack @Redis Hackathon

> Use Redis Stack (RedisJson) to replace Postgres as main storage, plus some refactoring


![stack change](https://dev-to-uploads.s3.amazonaws.com/uploads/articles/f661ebfetdrhnsd9ej6a.png)

- [README](../README.md)
- [Contributing](../CONTRIBUTING.md) 

## How it works

### How the data is stored:

The data is store as a document, for each day of the currency rates.

```json
{
   "2020-01-01": {
      "USD": 1,
      "EUR": 1.1,
      "AUD": 0.97
   }
}
```

### How the data is accessed:

In python codes, the data is accessed through a simple `get`
```python
r.json().get('2020-01-01')
```

### Performance Benchmarks

![postgres performance](https://dev-to-uploads.s3.amazonaws.com/uploads/articles/tee5tld95fsfs983ja7t.png)
![redis json performance](https://dev-to-uploads.s3.amazonaws.com/uploads/articles/cbavn3fsbabi2p41wlgh.png)

[Load test](../tests/load-test.js) is used here to measure the performance.
- same Machine (my personal macbook laptop)
- same spec for DB 
  - 10GB Volume
  - Same ARM64 Instance

The 2 key results here are `iterations` (higher is better) and `iteration_duration(avg)`(lower is better)

| Fact | Postgres | Redis Stack |
| :---: |:--------:|:-----------:|
| Iterations | 25.26/s  |   5.52/s    |
| Iteration Duration | 560.15ms |    5.53s    |

This performance benchmark is surprising to myself as well, Redis as a well performanced DB, 
in most of time, it give a very good result of performance.

In sum, this performance compare may not be objective, there are some potential reasons.

1.Min Specs for different DB are difference, even the spec for Postgres and Redis Stack here are the same, but their min spec requirements may be different.
   - [Postgres](https://www.enterprisedb.com/docs/supported-open-source/postgresql/installer/01_requirements_overview/): 1 GHz processor. 2 GB of RAM. 512 MB of HDD.
   - [Redis](https://docs.redis.com/latest/rs/administering/designing-production/hardware-requirements/): 2.6GHz(2 CPUs), 4 GB of Ram, 10 GD of HDD  (Redis Stack supposed to be higher) 

2.Decimal in Python as a class could not be saved directly as a JSON attribute in RedisJSOM, 
so it was stores as string, and it will be converted to Decimal when read. This may slow the APP down.

3.Query was not used (RedisSearch) was not used, so when query history data, a loop of `GET` are sent to DB, which is not efficient


In sum, it seems like Redis originally consume more Ram/CPU, so put it in the same instance of Postgres, it may not maximum Redis's power.
`Decimal Convert` and `Loop of Get` in Python slows the app too. (If anyone knows better about Redis to solve these problems, please let me know). So this comparing seems not very fair.





## Play around


```bash
docker run --name rate-api -p 8000:8000 -e REDIS_URL=redis://your-remote-redis:6379 -e USE_REDIS=1  ghcr.io/tim-hub/sanic-currency-exchange-rates-api:v2.3.0
```

## How to run it locally?


### Prerequisites

- python 3.10
- poetry >1.0
- redis stack  (RedisJSON 2)
- docker 20.10.xx (optional)


### Local installation and development


#### Local Python App Development

0. clone the repo `git clone https://github.com/tim-hub/sanic-currency-exchange-rates-api.git`
0. `export REDIS_URL = 'redis://localhost:6379'` (use your own redis stack url)
0. `export USE_REDIS = 1`
1. `poetry install`
2. `poetry run python src/main.py`


#### Through Docker 

`docker build -t rate-api . && docker run --name rate-api -t -i -e REDIS_URL=redis://your-remote-redis:6379 -e USE_REDIS=1 rate-api`

### Others
- How to Use Postgres DB at [Contributing](../CONTRIBUTING.md)

## Deployment

This app is wrapped in a docker container, so it could be deployer to any platform (which supports docker), From AWS, Heroku to K8s, 

the only requirements for it are 2 environment variables.
- REDIS_URL
- USE_REDIS


For example run in local machine:
```shell
docker run --name rate-api -p 8000:8000 -e REDIS_URL=redis://your-remote-redis:6379 -e USE_REDIS=1  ghcr.io/tim-hub/sanic-currency-exchange-rates-api:v2.3.0
```


## More Information about Redis Stack

Here some resources to help you quickly get started using Redis Stack. If you still have questions, feel free to ask them in the [Redis Discord](https://discord.gg/redis) or on [Twitter](https://twitter.com/redisinc).

### Getting Started

1. Sign up for a [free Redis Cloud account using this link](https://redis.info/try-free-dev-to) and use the [Redis Stack database in the cloud](https://developer.redis.com/create/rediscloud).
1. Based on the language/framework you want to use, you will find the following client libraries:
    - [Redis OM .NET (C#)](https://github.com/redis/redis-om-dotnet)
        - Watch this [getting started video](https://www.youtube.com/watch?v=ZHPXKrJCYNA)
        - Follow this [getting started guide](https://redis.io/docs/stack/get-started/tutorials/stack-dotnet/)
    - [Redis OM Node (JS)](https://github.com/redis/redis-om-node)
        - Watch this [getting started video](https://www.youtube.com/watch?v=KUfufrwpBkM)
        - Follow this [getting started guide](https://redis.io/docs/stack/get-started/tutorials/stack-node/)
    - [Redis OM Python](https://github.com/redis/redis-om-python)
        - Watch this [getting started video](https://www.youtube.com/watch?v=PPT1FElAS84)
        - Follow this [getting started guide](https://redis.io/docs/stack/get-started/tutorials/stack-python/)
    - [Redis OM Spring (Java)](https://github.com/redis/redis-om-spring)
        - Watch this [getting started video](https://www.youtube.com/watch?v=YhQX8pHy3hk)
        - Follow this [getting started guide](https://redis.io/docs/stack/get-started/tutorials/stack-spring/)

The above videos and guides should be enough to get you started in your desired language/framework. From there you can expand and develop your app. Use the resources below to help guide you further:

1. [Developer Hub](https://redis.info/devhub) - The main developer page for Redis, where you can find information on building using Redis with sample projects, guides, and tutorials.
1. [Redis Stack getting started page](https://redis.io/docs/stack/) - Lists all the Redis Stack features. From there you can find relevant docs and tutorials for all the capabilities of Redis Stack.
1. [Redis Rediscover](https://redis.com/rediscover/) - Provides use-cases for Redis as well as real-world examples and educational material
1. [RedisInsight - Desktop GUI tool](https://redis.info/redisinsight) - Use this to connect to Redis to visually see the data. It also has a CLI inside it that lets you send Redis CLI commands. It also has a profiler so you can see commands that are run on your Redis instance in real-time
1. Youtube Videos
    - [Official Redis Youtube channel](https://redis.info/youtube)
    - [Redis Stack videos](https://www.youtube.com/watch?v=LaiQFZ5bXaM&list=PL83Wfqi-zYZFIQyTMUU6X7rPW2kVV-Ppb) - Help you get started modeling data, using Redis OM, and exploring Redis Stack
    - [Redis Stack Real-Time Stock App](https://www.youtube.com/watch?v=mUNFvyrsl8Q) from Ahmad Bazzi
    - [Build a Fullstack Next.js app](https://www.youtube.com/watch?v=DOIWQddRD5M) with Fireship.io
    - [Microservices with Redis Course](https://www.youtube.com/watch?v=Cy9fAvsXGZA) by Scalable Scripts on freeCodeCamp