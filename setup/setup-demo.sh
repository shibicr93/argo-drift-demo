#!/bin/bash
set -e

echo "🎯 Setting up Enhanced ArgoCD Drift Detection Demo..."

# Apply custom health checks
kubectl apply -f k8s/argocd-config/custom-health-checks.yaml


# Restart ArgoCD server to load new health checks
kubectl rollout restart deployment/argocd-server -n argocd
kubectl rollout restart deployment/argocd-application-controller -n argocd

# Build hook images
echo "🐳 Building hook images..."
docker build -t drift-analyzer:latest -f docker/drift-analyzer/Dockerfile .
docker build -t audit-logger:latest -f docker/audit-logger/Dockerfile .
docker build -t emergency-rollback:latest -f docker/emergency-rollback/Dockerfile .

# Apply RBAC and controller
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/controller-deployment.yaml

# Deploy ApplicationSet (this creates all demo apps)
kubectl apply -f k8s/applicationset.yaml
# Test if custom health checks are applied
kubectl get applications -n argocd -o custom-columns=NAME:.metadata.name,HEALTH:.status.health.status,MESSAGE:.status.health.message

# Look for your custom health check messages
kubectl describe application your-app-name -n argocd


echo "⏳ Waiting for applications to be created..."
sleep 10

# Wait for applications to sync
kubectl wait --for=condition=available --timeout=300s deployment/guestbook-ui -n guestbook-low || true
kubectl wait --for=condition=available --timeout=300s deployment/guestbook-ui -n guestbook-medium || true
kubectl wait --for=condition=available --timeout=300s deployment/guestbook-ui -n guestbook-high || true

echo "✅ Enhanced demo setup complete!"
echo "📊 Monitor: kubectl logs -f deployment/argo-drift-controller -n argocd"
echo "🎮 Applications ready for drift simulation!"

