#!/bin/bash
set -e

REGISTRY="192.168.1.200:30000"
TAG="latest"

echo "🔨 Building and pushing inference..."
docker build -t $REGISTRY/neurotrade/inference:$TAG -f inference/Dockerfile .
docker push $REGISTRY/neurotrade/inference:$TAG

echo "🔨 Building and pushing streamlit-ui..."
docker build -t $REGISTRY/neurotrade/streamlit-ui:$TAG -f streamlit-ui/Dockerfile .
docker push $REGISTRY/neurotrade/streamlit-ui:$TAG

echo "🧠 Detecting Jetson environment for GPU build..."
if grep -q "tegra" /proc/device-tree/model 2>/dev/null || uname -a | grep -qi "tegra"; then
  echo "🚀 Jetson detected. Building GPU-enabled trainer image..."
  docker build \
      --platform linux/arm64/v8 \
      --build-arg BASE_IMAGE=nvcr.io/nvidia/l4t-pytorch:r35.3.1-pth2.0-py3 \
      -t $REGISTRY/neurotrade/trainer:$TAG \
      -f trainer/Dockerfile.gpu \
    .
else
  echo "⚠️ Non-GPU system detected. Building trainer with CPU fallback..."
  docker build -t $REGISTRY/neurotrade/trainer:$TAG -f trainer/Dockerfile .
fi

echo "📦 Pushing trainer..."
docker push $REGISTRY/neurotrade/trainer:$TAG

echo "✅ All images built and pushed successfully!"