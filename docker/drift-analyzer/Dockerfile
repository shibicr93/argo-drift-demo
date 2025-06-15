FROM python:3.9-slim

WORKDIR /app

RUN pip install kubernetes pyyaml

COPY docker/drift-analyzer/analyze_drift.py .

CMD ["python", "analyze_drift.py"]

