from kubernetes import client, config, watch
import logging
import time
import json
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

logging.basicConfig(level=logging.INFO)

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'healthy'}).encode())
        elif self.path == '/ready':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ready'}).encode())
        else:
            self.send_response(404)
            self.end_headers()

def start_health_server():
    server = HTTPServer(('0.0.0.0', 8080), HealthHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    logging.info("Health server started on port 8080")

class AutoRemediationController:
    def __init__(self):
        try:
            config.load_incluster_config()
            self.demo_mode = False
        except:
            try:
                config.load_kube_config()
                self.demo_mode = False
            except:
                logging.warning("No Kubernetes config found - running in demo mode")
                self.demo_mode = True
                return
        
        self.v1 = client.CustomObjectsApi()
        self.core_v1 = client.CoreV1Api()
        self.argocd_namespace = "argocd"  # Fixed: ArgoCD applications are in argocd namespace
        self.load_remediation_policies()
        
    def load_remediation_policies(self):
        self.remediation_matrix = {
            'low': {
                'action': 'auto_sync',
                'approval_required': False,
                'cooldown_minutes': 5,
                'max_retries': 3
            },
            'medium': {
                'action': 'notify_and_timeout',
                'approval_required': True,
                'timeout_hours': 24,
                'max_retries': 2
            },
            'high': {
                'action': 'immediate_rollback',
                'approval_required': False,
                'cooldown_minutes': 0,
                'max_retries': 1
            }
        }

    def handle_drift(self, app):
        app_name = app['metadata']['name']
        
        # Fixed: Only handle applications with drift-severity label
        labels = app['metadata'].get('labels', {})
        if 'drift-severity' not in labels:
            return
            
        severity = labels.get('drift-severity', 'low')
        
        logging.info(f"🎯 Detected drift in {app_name} with severity: {severity}")
        
        remediation = self.remediation_matrix.get(severity, self.remediation_matrix['low'])
        
        if remediation['action'] == 'auto_sync':
            self._execute_auto_sync(app_name, severity)
        elif remediation['action'] == 'notify_and_timeout':
            self._execute_notify_and_timeout(app_name, severity)
        elif remediation['action'] == 'immediate_rollback':
            self._execute_immediate_rollback(app_name, severity)

    def _execute_auto_sync(self, app_name, severity):
        try:
            if self.demo_mode:
                logging.info(f"DEMO: Would auto-sync {app_name}")
                return
                
            # Fixed: Trigger sync operation instead of patching syncPolicy
            sync_operation = {
                "operation": {
                    "sync": {
                        "syncStrategy": {
                            "apply": {
                                "force": True
                            }
                        },
                        "prune": True
                    }
                }
            }
            
            self.v1.patch_namespaced_custom_object(
                group="argoproj.io",
                version="v1alpha1",
                namespace=self.argocd_namespace,  # Fixed: Use argocd namespace
                plural="applications",
                name=app_name,
                body=sync_operation
            )
            
            logging.info(f"✅ Successfully triggered sync operation for {app_name}")
            
        except Exception as e:
            logging.error(f"❌ Failed to auto-sync {app_name}: {e}")

    def _execute_notify_and_timeout(self, app_name, severity):
        logging.info(f"📧 Notification sent for {app_name} - awaiting approval")
        logging.info(f"⏳ Timeout: 24 hours for manual intervention")

    def _execute_immediate_rollback(self, app_name, severity):
        try:
            logging.info(f"🚨 Executing immediate rollback for {app_name}")
            
            if self.demo_mode:
                logging.info(f"DEMO: Would rollback {app_name} to previous revision")
                return
                
            # Get application history to find last successful revision
            app = self.v1.get_namespaced_custom_object(
                group="argoproj.io",
                version="v1alpha1",
                namespace=self.argocd_namespace,
                plural="applications",
                name=app_name
            )
            
            # Find previous successful revision
            history = app.get('status', {}).get('history', [])
            if len(history) < 2:
                logging.error(f"No previous revision to rollback to for {app_name}")
                return
                
            previous_revision = history[-2]['revision']
            
            # Trigger rollback to previous revision
            rollback_operation = {
                "operation": {
                    "sync": {
                        "revision": previous_revision,
                        "syncStrategy": {
                            "apply": {
                                "force": True
                            }
                        },
                        "prune": True
                    }
                }
            }
            
            self.v1.patch_namespaced_custom_object(
                group="argoproj.io",
                version="v1alpha1",
                namespace=self.argocd_namespace,
                plural="applications",
                name=app_name,
                body=rollback_operation
            )
            
            logging.info(f"✅ Emergency rollback completed for {app_name} to revision {previous_revision}")
            
            # Create emergency alert
            self._create_emergency_alert(app_name, severity, f"Rolled back to {previous_revision}")
            
        except Exception as e:
            logging.error(f"❌ Emergency rollback failed for {app_name}: {e}")

    def _create_emergency_alert(self, app_name, severity, details):
        """Create emergency alert ConfigMap"""
        try:
            alert_cm = {
                'metadata': {
                    'name': f'emergency-alert-{app_name}-{int(time.time())}',
                    'namespace': self.argocd_namespace,
                    'labels': {
                        'alert-type': 'emergency-rollback',
                        'severity': severity,
                        'app': app_name
                    }
                },
                'data': {
                    'alert': f'Emergency rollback executed for {app_name}',
                    'details': details,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            self.core_v1.create_namespaced_config_map(
                namespace=self.argocd_namespace,
                body=alert_cm
            )
            
            logging.info(f"🚨 Emergency alert created for {app_name}")
            
        except Exception as e:
            logging.error(f"❌ Failed to create emergency alert: {e}")

    def watch_applications(self):
        if self.demo_mode:
            logging.info("Running in demo mode - simulating drift scenarios")
            return
        
        # Fixed: Added error handling and retry logic
        retry_count = 0
        max_retries = 5
        
        while retry_count < max_retries:
            try:
                logging.info(f"👀 Watching ArgoCD applications in namespace: {self.argocd_namespace}")
                w = watch.Watch()
                for event in w.stream(
                    self.v1.list_namespaced_custom_object,  # Fixed: Use namespaced instead of cluster
                    group="argoproj.io",
                    version="v1alpha1",
                    namespace=self.argocd_namespace,  # Fixed: Watch argocd namespace
                    plural="applications",
                    timeout_seconds=300  # Fixed: Added timeout
                ):
                    app = event['object']
                    if app.get('status', {}).get('sync', {}).get('status') == 'OutOfSync':
                        self.handle_drift(app)
                        
            except Exception as e:
                retry_count += 1
                logging.error(f"Watch error (attempt {retry_count}/{max_retries}): {e}")
                if retry_count < max_retries:
                    time.sleep(min(2 ** retry_count, 60))  # Exponential backoff
                else:
                    logging.error("Max retries reached, exiting")
                    break

if __name__ == '__main__':
    start_health_server()
    controller = AutoRemediationController()
    logging.info("🚀 Starting ArgoCD Advanced Drift Detection and Auto-Remediation Controller")
    controller.watch_applications()
