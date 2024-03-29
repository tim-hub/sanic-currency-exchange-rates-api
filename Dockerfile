FROM python:3.10-slim
ENV PYTHONUNBUFFERED 1
EXPOSE 8000

# Creating working directory
RUN mkdir /exchange_api
WORKDIR /exchange_api

# Copying requirements
ADD poetry.lock .
ADD pyproject.toml .

RUN pip install --no-cache-dir poetry
RUN poetry install

ADD src ./src

RUN ["chmod", "+x", "src/infra/start.sh"]
ENTRYPOINT ["src/infra/start.sh"]
