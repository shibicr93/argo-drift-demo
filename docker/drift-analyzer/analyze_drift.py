import os
import json
import yaml
from datetime import datetime
from kubernetes import client, config

def analyze_drift():
    """Analyze drift severity and recommend actions"""
    try:
        config.load_incluster_config()
    except:
        try:
            config.load_kube_config()
        except:
            print("Running in demo mode - no Kubernetes config")
            return simulate_analysis()
    
    app_name = os.getenv('APP_NAME', 'unknown')
    severity = os.getenv('SEVERITY', 'low')
    namespace = os.getenv('ARGOCD_APP_NAMESPACE', 'default')
    
    print(f"🔍 Analyzing drift for {app_name} with severity {severity}")
    
    # Get application resources
    v1 = client.AppsV1Api()
    core_v1 = client.CoreV1Api()
    
    drift_analysis = {
        'app_name': app_name,
        'severity': severity,
        'namespace': namespace,
        'timestamp': datetime.now().isoformat(),
        'drift_detected': True,
        'affected_resources': [],
        'recommended_action': get_recommended_action(severity),
        'risk_score': calculate_risk_score(severity)
    }
    
    try:
        # Analyze deployments
        deployments = v1.list_namespaced_deployment(namespace)
        for deployment in deployments.items:
            if check_deployment_drift(deployment):
                drift_analysis['affected_resources'].append({
                    'kind': 'Deployment',
                    'name': deployment.metadata.name,
                    'drift_type': 'replica_count'
                })
        
        # Analyze services
        services = core_v1.list_namespaced_service(namespace)
        for service in services.items:
            if check_service_drift(service):
                drift_analysis['affected_resources'].append({
                    'kind': 'Service',
                    'name': service.metadata.name,
                    'drift_type': 'service_type'
                })
                
    except Exception as e:
        print(f"Error analyzing resources: {e}")
        drift_analysis['error'] = str(e)
    
    # Save analysis results
    save_analysis_results(drift_analysis)
    
    print(f"✅ Analysis complete: {len(drift_analysis['affected_resources'])} resources affected")
    return drift_analysis

def check_deployment_drift(deployment):
    """Check if deployment has drifted"""
    # Simple drift detection - in production, compare with Git state
    return deployment.status.replicas != deployment.spec.replicas

def check_service_drift(service):
    """Check if service has drifted"""
    # Check for unexpected service type changes
    return service.spec.type != 'ClusterIP'

def calculate_risk_score(severity):
    """Calculate risk score based on severity"""
    risk_scores = {
        'low': 2,
        'medium': 5,
        'high': 8,
        'critical': 10
    }
    return risk_scores.get(severity, 1)

def get_recommended_action(severity):
    """Get recommended remediation action"""
    actions = {
        'low': 'auto_sync',
        'medium': 'notify_and_approve',
        'high': 'immediate_rollback',
        'critical': 'emergency_stop'
    }
    return actions.get(severity, 'manual_review')

def save_analysis_results(analysis):
    """Save analysis results for next hook"""
    os.makedirs('/results', exist_ok=True)
    with open('/results/analysis.json', 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print(f"📊 Analysis saved: Risk Score {analysis['risk_score']}/10")

def simulate_analysis():
    """Simulate analysis for demo mode"""
    return {
        'app_name': 'demo-app',
        'severity': 'medium',
        'drift_detected': True,
        'recommended_action': 'notify_and_approve',
        'risk_score': 5
    }

if __name__ == '__main__':
    analyze_drift()

