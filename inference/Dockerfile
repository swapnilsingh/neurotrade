FROM python:3.11-slim

WORKDIR /app

# Install dependencies early to leverage cache
COPY ./inference/requirements.txt .

RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy source code and config
COPY rl_agent /app/rl_agent
COPY utils /app/utils
COPY inference /app/inference
COPY feature_builder /app/feature_builder
COPY configs /app/configs

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

CMD ["python", "inference/run_inference_tick_mode.py"]
