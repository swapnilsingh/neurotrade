FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install Python dependencies early to leverage Docker cache
COPY ./inference/requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy only the relevant modules for inference
COPY inference /app/inference
COPY utils /app/utils
COPY core /app/core
COPY configs /app/configs

# Environment setup
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Updated default command
CMD ["python", "-u", "inference/main.py"]
