FROM python:3.9-slim

COPY ./analytics /analytics
COPY .env .
WORKDIR /analytics

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    jupyter \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "analytics.py", "--server.port", "8501", "--server.address=0.0.0.0"]
