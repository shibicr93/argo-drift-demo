---
marp: false
---

# ArgoCD Advanced Drift Detection and Auto-Remediation Demo

## Overview
This demo showcases a sophisticated drift detection and auto-remediation system for ArgoCD that combines:
- **Custom Health Checks** for real-time drift detection
- **Resource Hooks** for automated remediation workflows
- **ApplicationSet** for policy-driven application management
- **Dynamic Remediation Matrix** based on drift severity

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   ApplicationSet │───▶│ Custom Health    │───▶│ Resource Hooks  │
│   (Policy Mgmt) │    │ Checks (Detect)  │    │ (Remediate)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                       ┌─────────────────┐    ┌─────────────────┐
                       │ Drift Controller│    │ Audit & Alerts  │
                       │ (Orchestrate)   │    │ (Track & Notify)│
                       └─────────────────┘    └─────────────────┘
```

## Prerequisites

### Required Software
- Docker Desktop with Kubernetes enabled
- kubectl configured for Docker Desktop context
- ArgoCD CLI (optional, for manual operations)
- Git (for cloning the repository)

### Verify Setup
```bash
# Check Docker Desktop Kubernetes
kubectl config current-context  # Should show "docker-desktop"
kubectl get nodes               # Should show your local node

# Check available resources
kubectl top nodes               # Ensure sufficient CPU/Memory
```

## Quick Start Guide

### Step 1: Clone and Setup
```bash
git clone 
cd argo-drift-demo

# Make scripts executable
chmod +x setup/*.sh
```

### Step 2: Install ArgoCD
```bash
./setup/install-argocd.sh
```

**What this does:**
- Creates `argocd` namespace
- Installs ArgoCD with standard manifests
- Waits for ArgoCD to be ready
- Displays admin password for UI access

**Expected output:**
```
🚀 Installing ArgoCD on Docker Desktop Kubernetes...
⏳ Waiting for ArgoCD to be ready...
🔑 ArgoCD Admin Password: [generated-password]
✅ ArgoCD installed successfully!
```

### Step 3: Access ArgoCD UI (Optional)
```bash
# In a separate terminal (keep running)
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Visit https://localhost:8080
# Username: admin
# Password: (from Step 2 output)
```

### Step 4: Setup Demo Environment
```bash
./setup/setup-demo.sh
```

**What this does:**
- Builds Docker images for hook containers
- Applies custom health checks to ArgoCD
- Deploys the drift detection controller
- Creates ApplicationSet with three demo applications
- Configures RBAC permissions

**Expected output:**
```
🎯 Setting up Enhanced ArgoCD Drift Detection Demo...
🐳 Building hook images...
⏳ Waiting for applications to be created...
✅ Enhanced demo setup complete!
```

### Step 5: Verify Installation
```bash
# Check applications are created
kubectl get applications -n argocd

# Check controller is running
kubectl get pods -n argocd -l app=argo-drift-controller

# Check demo applications are deployed
kubectl get deployments -n guestbook-low
kubectl get deployments -n guestbook-medium  
kubectl get deployments -n guestbook-high
```

## Demo Components Explained

### 1. ApplicationSet Controller
**File:** `k8s/applicationset.yaml`

Creates three applications with different drift policies:

| Application | Severity | Auto-Remediate | Sync Policy | Hook Policy |
|-------------|----------|----------------|-------------|-------------|
| drift-demo-low | low | true | automated | auto-sync |
| drift-demo-medium | medium | conditional | manual | notify-approve |
| drift-demo-high | high | immediate | emergency | immediate-rollback |

**Key Features:**
- Template-based application generation
- Policy inheritance through labels
- Environment-specific configurations

### 2. Custom Health Checks
**File:** `k8s/argocd-config/custom-health-checks.yaml`

Extends ArgoCD's native health assessment:

```lua
-- Deployment drift detection
if obj.status.replicas ~= obj.spec.replicas then
  hs.status = "Progressing"
  hs.message = "Replica count drift detected"
end

-- Service drift detection  
if obj.spec.type == "LoadBalancer" then
  -- Custom logic for service changes
end
```

**Detects:**
- Replica count mismatches
- Service type changes
- Resource unavailability
- Configuration drift patterns

### 3. Resource Hooks Workflow
**Files:** `k8s/argocd-config/resource-hooks/`

Three-phase remediation workflow:

#### PreSync Hook (`presync-drift-analyzer.yaml`)
- **Wave:** -2 (runs first)
- **Purpose:** Analyze drift severity and affected resources
- **Output:** Analysis results for next phases

#### PostSync Hook (`postsync-audit-logger.yaml`)
- **Wave:** 2 (runs after sync)
- **Purpose:** Create audit trails and compliance logs
- **Output:** ConfigMaps with remediation history

#### SyncFail Hook (`syncfail-emergency-rollback.yaml`)
- **Trigger:** When sync operations fail
- **Purpose:** Execute emergency rollback procedures
- **Output:** Emergency alerts and rollback actions

### 4. Drift Detection Controller
**File:** `src/auto_remediation_controller.py`

Orchestrates the entire remediation process:

```python
# Dynamic remediation matrix
remediation_matrix = {
    'low': {'action': 'auto_sync', 'approval_required': False},
    'medium': {'action': 'notify_and_timeout', 'approval_required': True},
    'high': {'action': 'immediate_rollback', 'approval_required': False},
    'critical': {'action': 'emergency_stop', 'approval_required': False}
}
```

**Key Functions:**
- Watches ArgoCD applications for OutOfSync status
- Applies remediation policies based on severity
- Manages cooldown periods and retry logic
- Integrates with notification systems

## Live Demo Script

### Phase 1: Initial State Verification (2 minutes)

```bash
echo "=== Phase 1: Showing Initial State ==="

# Show ApplicationSet created applications
kubectl get applications -n argocd -l argocd.argoproj.io/application-set-name=drift-managed-applicationset

# Show all applications are healthy
kubectl get applications -n argocd -o custom-columns=NAME:.metadata.name,HEALTH:.status.health.status,SYNC:.status.sync.status

# Show controller is monitoring
kubectl logs deployment/argo-drift-controller -n argocd --tail=5
```

**Expected Output:**
```
NAME               HEALTH    SYNC
drift-demo-low     Healthy   Synced
drift-demo-medium  Healthy   Synced  
drift-demo-high    Healthy   Synced
```

### Phase 2: Low Severity Drift Demo (4 minutes)

```bash
echo "=== Phase 2: Low Severity Drift - Auto Remediation ==="

# Simulate low severity drift (replica scaling)
echo "🎯 Simulating replica count drift..."
kubectl scale deployment guestbook-ui --replicas=5 -n guestbook-low

# Watch custom health check detect drift
echo "👀 Watching health status change..."
kubectl get applications drift-demo-low -n argocd -w &
WATCH_PID=$!

# Wait for detection
sleep 10

# Show PreSync hook execution
echo "🔍 PreSync hook analyzing drift..."
kubectl get jobs -n guestbook-low | grep drift-analysis

# Show auto-sync triggered
echo "🔄 Auto-sync remediation in progress..."
kubectl get applications drift-demo-low -n argocd -o yaml | grep -A 5 "automated:"

# Show PostSync audit log created
echo "📋 PostSync audit log created..."
kubectl get configmaps -n argocd -l audit-type=drift-remediation | tail -1

# Stop watching
kill $WATCH_PID 2>/dev/null

echo "✅ Low severity drift auto-remediated!"
```

### Phase 3: Medium Severity Drift Demo (4 minutes)

```bash
echo "=== Phase 3: Medium Severity Drift - Approval Workflow ==="

# Simulate medium severity drift (service change)
echo "🎯 Simulating service configuration drift..."
kubectl patch service guestbook-ui -n guestbook-medium -p '{"spec":{"type":"LoadBalancer"}}'

# Show health check detection
echo "👀 Custom health check detecting service drift..."
kubectl get applications drift-demo-medium -n argocd -o custom-columns=NAME:.metadata.name,HEALTH:.status.health.status,MESSAGE:.status.health.message

# Show PreSync analysis
echo "🔍 PreSync hook analyzing medium severity drift..."
kubectl get jobs -n guestbook-medium | grep drift-analysis

# Show manual approval required
echo "⏳ Manual approval required - no auto-sync..."
kubectl get applications drift-demo-medium -n argocd -o yaml | grep -A 3 "syncPolicy:"

# Show notification would be sent
echo "📧 Notification sent (simulated):"
echo "   Subject: Medium severity drift detected in drift-demo-medium"
echo "   Action: Manual approval required within 24 hours"

# Demonstrate manual sync
echo "👤 Demonstrating manual approval and sync..."
kubectl patch application drift-demo-medium -n argocd --type='merge' -p='{"spec":{"syncPolicy":{"automated":{"prune":true,"selfHeal":true}}}}'

echo "✅ Medium severity drift requires human approval!"
```

### Phase 4: High Severity Drift Demo (3 minutes)

```bash
echo "=== Phase 4: High Severity Drift - Emergency Response ==="

# Simulate high severity drift (delete critical service)
echo "🚨 Simulating critical service deletion..."
kubectl delete service guestbook-ui -n guestbook-high

# Show immediate health degradation
echo "💔 Application health immediately degraded..."
kubectl get applications drift-demo-high -n argocd -o custom-columns=NAME:.metadata.name,HEALTH:.status.health.status,SYNC:.status.sync.status

# Show emergency remediation
echo "🚑 Emergency remediation triggered..."
kubectl get jobs -n guestbook-high | grep emergency

# Show emergency alerts created
echo "🚨 Emergency alerts generated..."
kubectl get configmaps -n argocd -l alert-type=emergency-rollback | tail -1

# Show immediate sync attempt
echo "⚡ Immediate sync/rollback in progress..."
kubectl get applications drift-demo-high -n argocd -o yaml | grep -A 5 "operation:"

echo "✅ High severity drift triggers immediate emergency response!"
```

### Phase 5: Audit and Observability (2 minutes)

```bash
echo "=== Phase 5: Audit Trail and Observability ==="

# Show complete audit trail
echo "📊 Complete audit trail from all remediation actions..."
kubectl get configmaps -n argocd -l audit-type=drift-remediation -o custom-columns=NAME:.metadata.name,APP:.metadata.labels.app,TIMESTAMP:.metadata.labels.timestamp

# Show application status summary
echo "📈 Application status summary..."
kubectl get applications -n argocd -o custom-columns=NAME:.metadata.name,HEALTH:.status.health.status,SYNC:.status.sync.status,SEVERITY:.metadata.labels.drift-severity

# Show controller metrics
echo "📊 Controller activity logs..."
kubectl logs deployment/argo-drift-controller -n argocd --tail=10

# Show ApplicationSet managing policies
echo "🎛️  ApplicationSet policy management..."
kubectl describe applicationset drift-managed-applicationset -n argocd | grep -A 10 "Template:"

echo "✅ Complete audit trail and observability demonstrated!"
```

## Troubleshooting Guide

### Common Issues

#### 1. Applications Not Created
```bash
# Check ApplicationSet status
kubectl describe applicationset drift-managed-applicationset -n argocd

# Check ArgoCD application controller logs
kubectl logs deployment/argocd-application-controller -n argocd

# Manually create application if needed
kubectl apply -f k8s/sample-apps/low-severity-app.yaml
```

#### 2. Custom Health Checks Not Working
```bash
# Verify health checks are loaded
kubectl get configmap argocd-cm -n argocd -o yaml | grep -A 20 "resource.customizations"

# Restart ArgoCD components
kubectl rollout restart deployment/argocd-server -n argocd
kubectl rollout restart deployment/argocd-application-controller -n argocd
```

#### 3. Hooks Not Executing
```bash
# Check hook job status
kubectl get jobs -A | grep -E "(drift-analysis|audit-logger|emergency-rollback)"

# Check hook logs
kubectl logs job/drift-analysis-presync -n guestbook-low

# Verify RBAC permissions
kubectl auth can-i create jobs --as=system:serviceaccount:argocd:argo-drift-controller
```

#### 4. Controller Not Starting
```bash
# Check controller pod status
kubectl describe pod -l app=argo-drift-controller -n argocd

# Check controller logs
kubectl logs deployment/argo-drift-controller -n argocd

# Check RBAC permissions
kubectl get clusterrolebinding argo-drift-controller
```

### Debug Commands

```bash
# Enable verbose logging
kubectl set env deployment/argo-drift-controller -n argocd LOG_LEVEL=DEBUG

# Check resource usage
kubectl top pods -n argocd

# Verify network connectivity
kubectl exec -it deployment/argo-drift-controller -n argocd -- ping argocd-server

# Check ArgoCD API access
kubectl exec -it deployment/argo-drift-controller -n argocd -- curl -k https://argocd-server/api/v1/applications
```

## Cleanup

### Quick Cleanup
```bash
./setup/cleanup.sh
```

### Manual Cleanup
```bash
# Remove demo applications
kubectl delete applications -n argocd -l argocd.argoproj.io/application-set-name=drift-managed-applicationset

# Remove ApplicationSet
kubectl delete applicationset drift-managed-applicationset -n argocd

# Remove controller
kubectl delete deployment argo-drift-controller -n argocd

# Remove ArgoCD (optional)
kubectl delete namespace argocd

# Remove demo namespaces
kubectl delete namespace guestbook-low guestbook-medium guestbook-high
```

## Customization

### Adding New Severity Levels
1. Update `remediation_matrix` in `src/auto_remediation_controller.py`
2. Add new severity rules in `src/drift_analyzer.py`
3. Create corresponding ApplicationSet entries
4. Update custom health checks if needed

### Integrating with External Systems
1. **Slack Integration:** Update webhook URL in `config/notification_config.yaml`
2. **PagerDuty:** Add integration key for critical alerts
3. **Monitoring:** Export metrics to Prometheus/Grafana
4. **ITSM:** Integrate with ServiceNow or Jira for approval workflows

### Production Considerations
1. **Security:** Implement proper RBAC and network policies
2. **Scalability:** Use persistent storage for audit logs
3. **Reliability:** Add circuit breakers and rate limiting
4. **Compliance:** Ensure audit logs meet regulatory requirements

## Demo Talking Points

### For Technical Audience
- "Notice how the ApplicationSet creates consistent policies across environments"
- "The custom health checks provide immediate drift visibility"
- "Resource hooks create a complete remediation lifecycle"
- "All actions are auditable and traceable"

### For Management Audience
- "Reduces MTTR from hours to minutes"
- "Prevents configuration drift from causing outages"
- "Provides complete audit trail for compliance"
- "Scales across hundreds of applications automatically"

## Next Steps

After the demo, consider:
1. **Pilot Implementation:** Start with non-production environments
2. **Team Training:** Ensure teams understand the remediation policies
3. **Monitoring Setup:** Implement proper observability stack
4. **Process Integration:** Align with existing change management processes

---

**Total Demo Time:** ~15 minutes + Q&A
**Audience Level:** Intermediate to Advanced DevOps/SRE
**Key Takeaway:** ArgoCD's native features can be combined to create sophisticated, automated drift management systems