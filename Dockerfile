FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY popper /app/popper
COPY src /app/src
COPY baseline_agents /app/baseline_agents
RUN pip install --no-cache-dir -e /app

COPY benchmark_scripts /app/benchmark_scripts
COPY dashboard /app/dashboard
COPY outputs /app/outputs

RUN mkdir -p /app/data /app/.logs && chmod -R 777 /app/data /app/.logs

RUN useradd -m nonrootuser
USER nonrootuser

ENTRYPOINT ["python"]
