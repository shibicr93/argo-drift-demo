#!/bin/bash
set -e

echo "🚀 Installing ArgoCD on Docker Desktop Kubernetes..."

# Create ArgoCD namespace
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -

# Install ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

echo "⏳ Waiting for ArgoCD to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd

# Get initial admin password
echo "🔑 ArgoCD Admin Password:"
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
echo ""

echo "✅ ArgoCD installed successfully!"
echo "🌐 Access ArgoCD UI: kubectl port-forward svc/argocd-server -n argocd 8080:443"
echo "🔗 Then visit: https://localhost:8080"

