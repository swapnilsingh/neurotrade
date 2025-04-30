FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY ./streamlit-ui/requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy necessary modules
COPY utils /app/utils
COPY configs /app/configs
COPY core /app/core
COPY streamlit-ui /app

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Start Streamlit app
CMD ["streamlit", "run", "dashboard_runner.py", "--server.port=8501", "--server.address=0.0.0.0"]
