# Deployment Guide

This document outlines comprehensive instructions for deploying the **Neurotrade** application using Docker, Kubernetes, and setting up a CI/CD pipeline for continuous integration and deployment.

---

## 🐳 Docker Deployment

Neurotrade supports containerized deployments using Docker Compose, simplifying both local development and production deployments.

### 🛠️ Build and Run Docker Containers:

```bash
docker-compose up -d --build
```

### 📃 Viewing Application Logs:

```bash
docker-compose logs -f
```

### 🛑 Stopping Containers:

```bash
docker-compose down
```

---

## ☸️ Kubernetes Deployment

Deploy Neurotrade on Kubernetes for scalable production-grade infrastructure.

### 📌 Prerequisites:

- Kubernetes cluster (e.g., K3s, Minikube)
- Kubectl configured for cluster interaction

### 🚀 Deployment Steps:

1. **Prepare Kubernetes Manifests**:
   Create necessary Kubernetes configuration files:
   - `deployment.yaml`
   - `service.yaml`
   - `ingress.yaml` (optional)

2. **Apply the manifests**:

```bash
kubectl apply -f k8s/
```

### ✅ Verify Deployment:

```bash
kubectl get pods -n neurotrade
kubectl logs <pod-name> -n neurotrade
```

### 🔄 Performing Updates:

Update Docker image and rollout changes:

```bash
kubectl set image deployment/neurotrade neurotrade-container=<your-image-name>:latest
```

---

## ⚡ CI/CD Pipeline Setup

Use GitHub Actions to automate build, test, and deployment processes.

### 📦 Workflow Overview:

- **Code Push**: Push changes to GitHub repository
- **Testing**: Automated unit and integration tests execution
- **Docker Image Build**: Build Docker image and push to Docker Hub
- **Kubernetes Deploy**: Automatically deploy updated Docker image to Kubernetes

### 🛠️ Configure CI/CD with GitHub Actions:

1. Create a GitHub Actions workflow file:

`./.github/workflows/ci-cd.yml`

```yaml
name: Neurotrade CI/CD

on:
  push:
    branches:
      - master

jobs:
  build-test-deploy:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout Repository
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install Dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Run Tests
      run: |
        pytest tests/

    - name: Docker Build and Push
      uses: docker/build-push-action@v5
      with:
        context: .
        push: true
        tags: your-dockerhub-username/neurotrade:latest
      env:
        DOCKERHUB_USERNAME: ${{ secrets.DOCKERHUB_USERNAME }}
        DOCKERHUB_TOKEN: ${{ secrets.DOCKERHUB_TOKEN }}

    - name: Deploy to Kubernetes
      uses: appleboy/ssh-action@master
      with:
        host: ${{ secrets.K8S_HOST }}
        username: ${{ secrets.K8S_USER }}
        key: ${{ secrets.K8S_SSH_KEY }}
        script: |
          kubectl set image deployment/neurotrade neurotrade-container=your-dockerhub-username/neurotrade:latest -n neurotrade
```

2. **Set Secrets** in GitHub Repository:
   - `DOCKERHUB_USERNAME`
   - `DOCKERHUB_TOKEN`
   - `K8S_HOST`
   - `K8S_USER`
   - `K8S_SSH_KEY`

---

## 📊 Monitoring and Logging

Logs from containers and Kubernetes pods should be monitored:

- Container logs (`docker-compose logs -f`)
- Kubernetes pod logs (`kubectl logs <pod-name>`)

Integrate additional monitoring tools like Prometheus and Grafana for advanced analytics.

---


