FROM python:3.9-slim

WORKDIR /app

RUN pip install kubernetes requests

COPY docker/emergency-rollback/emergency_rollback.py .

CMD ["python", "emergency_rollback.py"]

