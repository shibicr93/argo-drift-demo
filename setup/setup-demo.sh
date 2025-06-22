#!/bin/bash
set -e

echo "🎯 Setting up Enhanced ArgoCD Drift Detection Demo..."

# Build hook images
echo "🐳 Building hook images..."
docker build -t drift-analyzer:latest -f docker/drift-analyzer/Dockerfile .
docker build -t audit-logger:latest -f docker/audit-logger/Dockerfile .
docker build -t emergency-rollback:latest -f docker/emergency-rollback/Dockerfile .

# Apply RBAC
echo "🔐 Applying RBAC for ArgoCD..."
kubectl apply -f k8s/rbac.yaml

# Build the main controller image
echo "🐳 Building Argo Drift Controller image..."
docker build -t argo-drift-controller:latest -f docker/Dockerfile .
# Deploy the controller
echo "🚀 Deploying Argo Drift Controller..."
kubectl apply -f k8s/controller-deployment.yaml

# Apply resource hooks
echo "🔧 Applying resource hooks..."
kubectl apply -f k8s/argocd-config/resource-hooks

# Deploy ApplicationSet (this creates all demo apps)
echo "📦 Deploying ApplicationSet for demo applications..."
kubectl apply -f k8s/applicationset.yaml
# Test if custom health checks are applied
kubectl get applications -n argocd -o custom-columns=NAME:.metadata.name,HEALTH:.status.health.status,MESSAGE:.status.health.message


echo "⏳ Waiting for applications to be created..."
sleep 10

# Wait for applications to sync
echo "⏳ Waiting for applications to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/low-severity-app -n enhanced-low-severity || true
kubectl wait --for=condition=available --timeout=300s deployment/medium-severity-app -n enhanced-medium-severity || true
kubectl wait --for=condition=available --timeout=300s deployment/high-severity-app -n enhanced-high-severity || true

echo "✅ Enhanced demo setup complete!"
echo "📊 Monitor: kubectl logs -f deployment/argo-drift-controller -n argocd"
echo "🎮 Applications ready for drift simulation!"

