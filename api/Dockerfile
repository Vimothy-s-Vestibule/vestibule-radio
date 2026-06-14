FROM python:3.13-slim

WORKDIR /app

COPY api/requirements.txt ./api/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt

COPY api ./api

EXPOSE 8002

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8002"]
