FROM python:3.9-slim

WORKDIR /app

RUN pip install kubernetes

COPY docker/audit-logger/log_audit.py .

CMD ["python", "log_audit.py"]

