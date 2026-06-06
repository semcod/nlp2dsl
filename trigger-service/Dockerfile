FROM python:3.12-slim

WORKDIR /app
COPY trigger-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY trigger-service/app ./app

EXPOSE 8020
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8020"]
