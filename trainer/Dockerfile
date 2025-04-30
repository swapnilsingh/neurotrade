FROM python:3.9-slim

WORKDIR /app

COPY trainer/requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY trainer /app/trainer
COPY utils /app/utils
COPY core /app/core
COPY configs /app/configs

RUN echo "🔍 Listing /app/configs contents:" && ls -l /app/configs

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

CMD ["python3", "trainer/main.py"]
