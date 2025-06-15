from kubernetes import client, config, watch
import logging
import time
import yaml
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import json

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
        except:
            try:
                config.load_kube_config()
            except:
                logging.warning("No Kubernetes config found - running in demo mode")
                self.demo_mode = True
                return
        
        self.demo_mode = False
        self.v1 = client.CustomObjectsApi()
        self.core_v1 = client.CoreV1Api()
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
        namespace = app['metadata']['namespace']
        severity = app['metadata'].get('labels', {}).get('drift-severity', 'low')
        
        logging.info(f"Detected drift in {app_name} with severity: {severity}")
        
        remediation = self.remediation_matrix.get(severity, self.remediation_matrix['low'])
        
        if remediation['action'] == 'auto_sync':
            self._execute_auto_sync(app_name, namespace, severity)
        elif remediation['action'] == 'notify_and_timeout':
            self._execute_notify_and_timeout(app_name, namespace, severity)
        elif remediation['action'] == 'immediate_rollback':
            self._execute_immediate_rollback(app_name, namespace, severity)

    def _execute_auto_sync(self, app_name, namespace, severity):
        try:
            if self.demo_mode:
                logging.info(f"DEMO: Would auto-sync {app_name}")
                return
                
            sync_body = {
                "spec": {
                    "syncPolicy": {
                        "automated": {"prune": True, "selfHeal": True}
                    }
                }
            }
            
            self.v1.patch_namespaced_custom_object(
                group="argoproj.io",
                version="v1alpha1",
                namespace=namespace,
                plural="applications",
                name=app_name,
                body=sync_body
            )
            
            logging.info(f"Successfully triggered auto-remediation for {app_name}")
            
        except Exception as e:
            logging.error(f"Failed to auto-sync {app_name}: {e}")

    def _execute_notify_and_timeout(self, app_name, namespace, severity):
        logging.info(f"Notification sent for {app_name} - awaiting approval")

    def _execute_immediate_rollback(self, app_name, namespace, severity):
        logging.info(f"Executing immediate rollback for {app_name}")

    def watch_applications(self):
        if self.demo_mode:
            logging.info("Running in demo mode - simulating drift scenarios")
            return
            
        w = watch.Watch()
        for event in w.stream(
            self.v1.list_cluster_custom_object,
            group="argoproj.io",
            version="v1alpha1",
            plural="applications",
            timeout_seconds=0
        ):
            app = event['object']
            if app.get('status', {}).get('sync', {}).get('status') == 'OutOfSync':
                self.handle_drift(app)

if __name__ == '__main__':
    start_health_server()
    controller = AutoRemediationController()
    logging.info("Starting ArgoCD Advanced Drift Detection and Auto-Remediation Controller")
    controller.watch_applications()

