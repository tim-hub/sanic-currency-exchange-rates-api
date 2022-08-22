FROM python:3.10-slim
ENV PYTHONUNBUFFERED 1
EXPOSE 8000

# Creating working directory
RUN mkdir /exchange_api
WORKDIR /exchange_api

# Copying requirements
ADD src/poetry.lock .
ADD src/pyproject.toml .

RUN pip install poetry
RUN poetry install

ADD src .

RUN ["chmod", "+x", "infra/start.sh"]
CMD ["infra/start.sh"]
