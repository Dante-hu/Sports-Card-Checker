# Use an official Python image
FROM python:3.12-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory inside the container
WORKDIR /app

# Install system deps (psycopg2 + friends)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
  && rm -rf /var/lib/apt/lists/*

# Copy only requirements first (for better caching if you add one later)
# If you have a requirements.txt in server/, uncomment these two lines:
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# If you DON'T have a requirements.txt yet, we’ll just copy everything and install from setup, or you can generate one.
# For now, we copy the whole server folder:
COPY . .

# Install Python dependencies (from requirements.txt if you add it inside server/)
# If you’re using requirements.txt, comment this out and rely on the lines above
RUN pip install --no-cache-dir -r requirements.txt || true

# Environment variables for Flask
ENV FLASK_APP=app:create_app
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# Expose the port Flask runs on
EXPOSE 5000

# Default DATABASE_URL can be overridden at runtime (recommended).
# NOTE: this is just a fallback; you'll usually override it with -e DATABASE_URL=...
ENV DATABASE_URL="postgresql://postgres:postgres123@localhost:5433/sports_card_checker"

# Run Flask in production-ish mode (turn off debug)
ENV FLASK_ENV=production

# Command to run the app
CMD ["python", "-m", "flask", "run"]

