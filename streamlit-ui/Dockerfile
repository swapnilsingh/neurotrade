FROM python:3.11-slim

WORKDIR /app

COPY ./streamlit-ui/requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY utils /app/utils
COPY configs /app/configs
COPY streamlit-ui /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
