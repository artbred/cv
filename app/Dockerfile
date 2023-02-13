FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9-slim

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y build-essential

COPY ./app /app
WORKDIR /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt