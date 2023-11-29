FROM python:3.11.4-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code/

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
