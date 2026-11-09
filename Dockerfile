FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENV SHIKSHA_GENERATE_MODE=local
ENV SHIKSHA_DB=/data/shiksha.sqlite
ENV SHIKSHA_OFFLINE_DB=/data/offline_queue.sqlite
ENV SHIKSHA_MONTHLY_CAP_USD=5

EXPOSE 8000
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
