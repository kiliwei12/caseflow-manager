FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p data

EXPOSE 5066
CMD ["sh", "-c", "python -c 'from app import init_db; init_db()' && python seed_demo.py && gunicorn --bind 0.0.0.0:${PORT:-5066} --workers 2 --access-logfile - app:app"]
