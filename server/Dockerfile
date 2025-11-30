FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=app
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

# Gunicorn will call create_app() in app/__init__.py
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:create_app()"]
