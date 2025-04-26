#!/bin/bash
set -e

NAMESPACE=neurotrade

if [[ "$1" == "start" ]]; then
  echo "📦 Ensuring namespace '$NAMESPACE' exists..."
  kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

  echo '🚀 Deploying Redis'
  kubectl apply -f deployment/k3s/redis.yaml -n $NAMESPACE
  kubectl rollout status deployment/redis -n $NAMESPACE

  echo '🚀 Deploying Inference'
  kubectl apply -f deployment/k3s/inference.yaml -n $NAMESPACE
  kubectl rollout status deployment/inference -n $NAMESPACE

  echo '🚀 Deploying Trainer'
  kubectl apply -f deployment/k3s/trainer.yaml -n $NAMESPACE
  kubectl rollout status deployment/trainer -n $NAMESPACE

  if [[ -f deployment/k3s/streamlit-ui.yaml ]]; then
    echo '🚀 Deploying Streamlit UI'
    kubectl apply -f deployment/k3s/streamlit-ui.yaml -n $NAMESPACE
    kubectl rollout status deployment/streamlit-ui -n $NAMESPACE
  else
    echo "⚠️ Skipping Streamlit UI deployment (file not found)"
  fi

  echo "✅ All Neurotrade components deployed successfully into '$NAMESPACE'!"

elif [[ "$1" == "stop" ]]; then
  echo "🛑 Stopping Neurotrade deployments in namespace '$NAMESPACE'..."
  kubectl delete -f deployment/k3s/streamlit-ui.yaml -n $NAMESPACE --ignore-not-found
  kubectl delete -f deployment/k3s/trainer.yaml -n $NAMESPACE --ignore-not-found
  kubectl delete -f deployment/k3s/inference.yaml -n $NAMESPACE --ignore-not-found
  kubectl delete -f deployment/k3s/redis.yaml -n $NAMESPACE --ignore-not-found

  echo "✅ All Neurotrade deployments stopped. Namespace '$NAMESPACE' retained."

else
  echo "❗ Usage: $0 {start|stop}"
  exit 1
fi
