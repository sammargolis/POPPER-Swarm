FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY popper /app/popper
COPY src /app/src
COPY baseline_agents /app/baseline_agents
COPY benchmark_scripts /app/benchmark_scripts
COPY dashboard /app/dashboard
COPY outputs /app/outputs

RUN mkdir -p /app/data /app/.logs && chmod -R 777 /app/data /app/.logs

RUN useradd -m nonrootuser
USER nonrootuser

ENV PYTHONPATH="/app/src:/app"

ENTRYPOINT ["python"]
