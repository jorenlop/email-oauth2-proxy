FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY relay_smtp.py .
COPY .env .
COPY token_cache.json .

ENV PYTHONUNBUFFERED=1  

CMD ["python", "/app/relay_smtp.py"]