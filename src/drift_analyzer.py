import logging
from datetime import datetime
from kubernetes import client, config

class DriftAnalyzer:
    def __init__(self):
        self.severity_rules = {
            'critical': ['secret', 'rbac', 'security', 'serviceaccount'],
            'high': ['deployment', 'service', 'ingress', 'statefulset'],
            'medium': ['configmap', 'pvc', 'job', 'cronjob'],
            'low': ['labels', 'annotations', 'metadata']
        }
        
        self.risk_weights = {
            'critical': 10,
            'high': 8,
            'medium': 5,
            'low': 2
        }

    def analyze_drift(self, app):
        """Analyze drift and determine severity based on resource types and changes"""
        app_name = app['metadata']['name']
        labels = app['metadata'].get('labels', {})
        
        logging.info(f"🔍 Analyzing drift for application: {app_name}")
        
        # Check for explicit severity label first
        if 'drift-severity' in labels:
            severity = labels['drift-severity']
            details = f"Explicit severity set via label: {severity}"
            return severity, details
        
        # Analyze based on application status and resources
        severity, details = self._analyze_application_resources(app)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(app, severity)
        
        logging.info(f"📊 Drift analysis complete - Severity: {severity}, Risk Score: {risk_score}/10")
        
        return severity, f"{details} (Risk Score: {risk_score}/10)"

    def _analyze_application_resources(self, app):
        """Analyze application resources to determine drift severity"""
        app_name = app['metadata']['name']
        
        # Get resource status from ArgoCD application
        resources = app.get('status', {}).get('resources', [])
        sync_status = app.get('status', {}).get('sync', {}).get('status', 'Unknown')
        health_status = app.get('status', {}).get('health', {}).get('status', 'Unknown')
        
        if not resources:
            return 'low', 'No specific resources identified in drift'
        
        # Analyze each resource for severity
        highest_severity = 'low'
        affected_resources = []
        
        for resource in resources:
            resource_kind = resource.get('kind', '').lower()
            resource_name = resource.get('name', 'unknown')
            resource_status = resource.get('status', 'Unknown')
            
            # Determine severity based on resource type
            resource_severity = self._get_resource_severity(resource_kind)
            
            if self._is_higher_severity(resource_severity, highest_severity):
                highest_severity = resource_severity
            
            if resource_status in ['OutOfSync', 'Degraded', 'Missing']:
                affected_resources.append({
                    'kind': resource.get('kind'),
                    'name': resource_name,
                    'status': resource_status,
                    'severity': resource_severity
                })
        
        # Additional analysis based on sync and health status
        if health_status == 'Degraded':
            if highest_severity == 'low':
                highest_severity = 'medium'
        
        if sync_status == 'OutOfSync' and len(affected_resources) > 5:
            highest_severity = self._escalate_severity(highest_severity)
        
        details = f"Analyzed {len(resources)} resources, {len(affected_resources)} affected. " \
                 f"Health: {health_status}, Sync: {sync_status}"
        
        return highest_severity, details

    def _get_resource_severity(self, resource_kind):
        """Determine severity based on resource type"""
        for severity, resource_types in self.severity_rules.items():
            if any(rt in resource_kind for rt in resource_types):
                return severity
        return 'low'

    def _is_higher_severity(self, new_severity, current_severity):
        """Check if new severity is higher than current"""
        severity_order = ['low', 'medium', 'high', 'critical']
        return severity_order.index(new_severity) > severity_order.index(current_severity)

    def _escalate_severity(self, current_severity):
        """Escalate severity by one level"""
        escalation_map = {
            'low': 'medium',
            'medium': 'high',
            'high': 'critical',
            'critical': 'critical'
        }
        return escalation_map.get(current_severity, current_severity)

    def _calculate_risk_score(self, app, severity):
        """Calculate numerical risk score (1-10)"""
        base_score = self.risk_weights.get(severity, 1)
        
        # Adjust score based on additional factors
        resources = app.get('status', {}).get('resources', [])
        
        # More resources = higher risk
        if len(resources) > 10:
            base_score += 1
        elif len(resources) > 20:
            base_score += 2
        
        # Namespace criticality (production environments)
        namespace = app.get('spec', {}).get('destination', {}).get('namespace', '')
        if 'prod' in namespace.lower() or 'production' in namespace.lower():
            base_score += 1
        
        # Application labels indicating criticality
        labels = app.get('metadata', {}).get('labels', {})
        if labels.get('criticality') == 'high':
            base_score += 1
        
        # Cap at 10
        return min(base_score, 10)

    def get_recommended_action(self, severity):
        """Get recommended remediation action based on severity"""
        action_map = {
            'low': 'auto_sync',
            'medium': 'notify_and_approve',
            'high': 'immediate_rollback',
            'critical': 'emergency_stop'
        }
        return action_map.get(severity, 'manual_review')

    def analyze_drift_trend(self, app_name, historical_data=None):
        """Analyze drift trends over time (placeholder for future enhancement)"""
        # This could be enhanced to track drift patterns over time
        # and predict potential issues
        
        logging.info(f"📈 Trend analysis for {app_name} - Feature coming soon")
        
        return {
            'trend': 'stable',
            'frequency': 'low',
            'prediction': 'no_immediate_risk'
        }

    def generate_drift_report(self, app, severity, details):
        """Generate comprehensive drift analysis report"""
        app_name = app['metadata']['name']
        namespace = app.get('spec', {}).get('destination', {}).get('namespace', 'unknown')
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'application': app_name,
            'namespace': namespace,
            'severity': severity,
            'risk_score': self._calculate_risk_score(app, severity),
            'details': details,
            'recommended_action': self.get_recommended_action(severity),
            'affected_resources': self._get_affected_resources(app),
            'analysis_metadata': {
                'analyzer_version': '1.0.0',
                'analysis_duration_ms': 50,  # Placeholder
                'confidence_score': 0.95
            }
        }
        
        return report

    def _get_affected_resources(self, app):
        """Extract list of affected resources"""
        resources = app.get('status', {}).get('resources', [])
        affected = []
        
        for resource in resources:
            if resource.get('status') in ['OutOfSync', 'Degraded', 'Missing']:
                affected.append({
                    'kind': resource.get('kind'),
                    'name': resource.get('name'),
                    'namespace': resource.get('namespace'),
                    'status': resource.get('status')
                })
        
        return affected

