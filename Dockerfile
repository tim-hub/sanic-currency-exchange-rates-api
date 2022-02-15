FROM python:3.7
ENV PYTHONUNBUFFERED 1
EXPOSE 8000

# Creating working directory
RUN mkdir /exchange_api
WORKDIR /exchange_api

# Copying requirements
ADD . .

RUN pip install -r requirements.txt

CMD ["python", "main.py"]