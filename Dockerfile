FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY practice_api.py .
COPY copilot/ ./copilot/
COPY tests/ ./tests/

CMD ["python", "-m", "uvicorn", "practice_api:app", "--host", "0.0.0.0", "--port", "8000"]