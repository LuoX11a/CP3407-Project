FROM python:3.11-slim

WORKDIR /app

# 2026-08-03: Final demo — include ML model (ensure .dockerignore allows *.joblib)
ENV PYTHONPATH=/app/backend
ENV MODEL_PATH=ml/model/carpark_predictor.joblib

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD python -m uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}
