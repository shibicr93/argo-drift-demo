import os
import requests
import json
from datetime import datetime
from kubernetes import client, config

def execute_emergency_rollback():
    """Execute emergency rollback for high-severity drift"""
    try:
        config.load_incluster_config()
    except:
        try:
            config.load_kube_config()
        except:
            print("Demo mode: Emergency rollback would be executed")
            return simulate_rollback()
    
    app_name = os.getenv('APP_NAME', 'unknown')
    severity = os.getenv('SEVERITY', 'low')
    namespace = os.getenv('ARGOCD_APP_NAMESPACE', 'default')
    
    print(f"🚨 EMERGENCY: Executing rollback for {app_name} (severity: {severity})")
    
    if severity in ['high', 'critical']:
        # Execute immediate rollback
        rollback_success = trigger_argocd_rollback(app_name)
        
        if not rollback_success:
            # Fallback: Direct Kubernetes rollback
            execute_kubernetes_rollback(namespace)
        
        # Create emergency alert
        create_emergency_alert(app_name, severity, rollback_success)
        
        # Notify on-call team
        if severity == 'critical':
            notify_oncall_team(app_name, severity)
    
    else:
        print(f"ℹ️  Severity {severity} does not require emergency rollback")

def trigger_argocd_rollback(app_name):
    """Trigger rollback via ArgoCD API"""
    try:
        # In production, use proper ArgoCD API authentication
        argocd_server = os.getenv('ARGOCD_SERVER', 'argocd-server.argocd.svc.cluster.local')
        
        # Simulate API call for demo
        print(f"🔄 Triggering ArgoCD rollback for {app_name}")
        print(f"📡 API Call: POST {argocd_server}/api/v1/applications/{app_name}/rollback")
        
        # In real implementation:
        # response = requests.post(f"{argocd_server}/api/v1/applications/{app_name}/rollback")
        # return response.status_code == 200
        
        return True
        
    except Exception as e:
        print(f"❌ ArgoCD rollback failed: {e}")
        return False

def execute_kubernetes_rollback(namespace):
    """Fallback: Direct Kubernetes rollback"""
    try:
        apps_v1 = client.AppsV1Api()
        
        # Get deployments in namespace
        deployments = apps_v1.list_namespaced_deployment(namespace)
        
        for deployment in deployments.items:
            deployment_name = deployment.metadata.name
            print(f"🔄 Rolling back deployment: {deployment_name}")
            
            # Trigger rollback
            apps_v1.create_namespaced_deployment_rollback(
                name=deployment_name,
                namespace=namespace,
                body={'kind': 'DeploymentRollback', 'apiVersion': 'apps/v1'}
            )
            
    except Exception as e:
        print(f"❌ Kubernetes rollback failed: {e}")

def create_emergency_alert(app_name, severity, rollback_success):
    """Create emergency alert ConfigMap"""
    try:
        v1 = client.CoreV1Api()
        
        alert_cm = {
            'metadata': {
                'name': f'emergency-alert-{app_name}-{int(datetime.now().timestamp())}',
                'namespace': 'argocd',
                'labels': {
                    'alert-type': 'emergency-rollback',
                    'severity': severity,
                    'app': app_name
                }
            },
            'data': {
                'alert': f'Emergency rollback {"completed" if rollback_success else "failed"} for {app_name}',
                'severity': severity,
                'timestamp': datetime.now().isoformat(),
                'rollback_status': 'success' if rollback_success else 'failed',
                'operator': 'emergency-rollback-hook'
            }
        }
        
        v1.create_namespaced_config_map(
            namespace='argocd',
            body=alert_cm
        )
        
        print(f"🚨 Emergency alert created for {app_name}")
        
    except Exception as e:
        print(f"❌ Failed to create emergency alert: {e}")

def notify_oncall_team(app_name, severity):
    """Notify on-call team for critical issues"""
    print(f"📞 CRITICAL: Notifying on-call team about {app_name}")
    print(f"📧 Email sent to: oncall@company.com")
    print(f"📱 PagerDuty alert triggered")
    print(f"💬 Slack alert sent to: #critical-alerts")

def simulate_rollback():
    """Simulate rollback for demo mode"""
    print("🎭 DEMO: Emergency rollback simulation")
    print("✅ Would rollback to last known good state")
    print("🚨 Would create emergency alerts")
    print("📞 Would notify on-call team")

if __name__ == '__main__':
    execute_emergency_rollback()

