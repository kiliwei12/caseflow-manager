FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p data

EXPOSE 8080
CMD ["sh", "-c", "export SECRET_KEY=\"${SECRET_KEY:-$(python -c 'import secrets; print(secrets.token_hex(32))')}\" && if [ \"${CASEFLOW_DEMO_MODE:-0}\" != \"1\" ]; then python -c 'from app import init_db; init_db()'; fi && gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 2 --access-logfile - app:app"]
