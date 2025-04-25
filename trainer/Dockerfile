# Use ARG to make base image configurable
FROM python:3.9-slim

WORKDIR /app

COPY trainer/requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY rl_agent /app/rl_agent
COPY utils /app/utils
COPY trainer /app/trainer
COPY configs /app/configs

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app/trainer
CMD ["python3", "trainer_runner.py"]
