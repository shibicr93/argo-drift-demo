#!/bin/bash
echo "🧹 Cleaning up demo environment..."

kubectl delete -f k8s/sample-apps/ --ignore-not-found=true
kubectl delete -f k8s/controller-deployment.yaml --ignore-not-found=true
kubectl delete -f k8s/rbac.yaml --ignore-not-found=true
kubectl delete namespace argocd --ignore-not-found=true

echo "✅ Cleanup complete!"

