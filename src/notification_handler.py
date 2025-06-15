import logging
import json
import requests
import smtplib
from datetime import datetime
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

class NotificationHandler:
    def __init__(self):
        self.channels = {
            'slack': {
                'webhook_url': None,  # Set from config
                'channel': '#drift-alerts',
                'username': 'ArgoCD Drift Bot'
            },
            'email': {
                'smtp_server': 'smtp.company.com',
                'smtp_port': 587,
                'from_address': 'argocd-alerts@company.com',
                'to_addresses': ['devops@company.com', 'sre@company.com']
            },
            'pagerduty': {
                'integration_key': None,  # Set from config
                'service_id': None
            }
        }
        
        self.templates = {
            'drift_detected': {
                'title': '🚨 Configuration Drift Detected',
                'slack': self._slack_drift_template,
                'email': self._email_drift_template
            },
            'remediation_complete': {
                'title': '✅ Drift Remediation Complete',
                'slack': self._slack_remediation_template,
                'email': self._email_remediation_template
            },
            'emergency_alert': {
                'title': '🚨 EMERGENCY: Critical Drift Detected',
                'slack': self._slack_emergency_template,
                'email': self._email_emergency_template
            }
        }

    def send_notification(self, app_name, message, severity='medium', channels=None):
        """Send standard notification to configured channels"""
        if channels is None:
            channels = self._get_channels_for_severity(severity)
        
        notification_data = {
            'app_name': app_name,
            'message': message,
            'severity': severity,
            'timestamp': datetime.now().isoformat()
        }
        
        logging.info(f"📢 Sending {severity} notification for {app_name}")
        
        for channel in channels:
            try:
                if channel == 'slack':
                    self._send_slack_notification(notification_data, 'drift_detected')
                elif channel == 'email':
                    self._send_email_notification(notification_data, 'drift_detected')
                elif channel == 'pagerduty':
                    self._send_pagerduty_alert(notification_data)
                    
            except Exception as e:
                logging.error(f"Failed to send {channel} notification: {e}")

    def send_critical_alert(self, app_name, message, details=None):
        """Send critical alert with immediate escalation"""
        alert_data = {
            'app_name': app_name,
            'message': message,
            'details': details or {},
            'severity': 'critical',
            'timestamp': datetime.now().isoformat(),
            'alert_id': f"CRIT-{app_name}-{int(datetime.now().timestamp())}"
        }
        
        logging.critical(f"🚨 CRITICAL ALERT: {app_name} - {message}")
        
        # Send to all channels for critical alerts
        try:
            self._send_slack_notification(alert_data, 'emergency_alert')
            self._send_email_notification(alert_data, 'emergency_alert')
            self._send_pagerduty_alert(alert_data, severity='critical')
            
            # Additional escalation for critical alerts
            self._trigger_oncall_escalation(alert_data)
            
        except Exception as e:
            logging.error(f"Failed to send critical alert: {e}")

    def send_remediation_complete(self, app_name, action, status, duration=None):
        """Send notification when remediation is complete"""
        remediation_data = {
            'app_name': app_name,
            'action': action,
            'status': status,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        }
        
        logging.info(f"✅ Remediation complete notification for {app_name}")
        
        try:
            self._send_slack_notification(remediation_data, 'remediation_complete')
            self._send_email_notification(remediation_data, 'remediation_complete')
            
        except Exception as e:
            logging.error(f"Failed to send remediation notification: {e}")

    def _get_channels_for_severity(self, severity):
        """Get notification channels based on severity"""
        channel_matrix = {
            'low': ['slack'],
            'medium': ['slack', 'email'],
            'high': ['slack', 'email', 'pagerduty'],
            'critical': ['slack', 'email', 'pagerduty']
        }
        return channel_matrix.get(severity, ['slack'])

    def _send_slack_notification(self, data, template_type):
        """Send Slack notification"""
        webhook_url = self.channels['slack'].get('webhook_url')
        if not webhook_url:
            logging.info(f"DEMO: Would send Slack notification - {template_type}")
            self._log_demo_notification('Slack', data, template_type)
            return
        
        message = self.templates[template_type]['slack'](data)
        
        payload = {
            'channel': self.channels['slack']['channel'],
            'username': self.channels['slack']['username'],
            'text': message,
            'icon_emoji': self._get_emoji_for_severity(data.get('severity', 'medium'))
        }
        
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 200:
            logging.info(f"✅ Slack notification sent successfully")
        else:
            logging.error(f"❌ Slack notification failed: {response.status_code}")

    def _send_email_notification(self, data, template_type):
        """Send email notification"""
        smtp_config = self.channels['email']
        
        # Demo mode - just log
        logging.info(f"DEMO: Would send email notification - {template_type}")
        self._log_demo_notification('Email', data, template_type)
        return
        
        # Production email sending code would go here
        # msg = MimeMultipart()
        # msg['From'] = smtp_config['from_address']
        # msg['To'] = ', '.join(smtp_config['to_addresses'])
        # msg['Subject'] = self.templates[template_type]['title']
        # ... SMTP implementation

    def _send_pagerduty_alert(self, data, severity='high'):
        """Send PagerDuty alert"""
        integration_key = self.channels['pagerduty'].get('integration_key')
        if not integration_key:
            logging.info(f"DEMO: Would send PagerDuty alert - {severity}")
            self._log_demo_notification('PagerDuty', data, 'alert')
            return
        
        # PagerDuty Events API v2 implementation would go here
        logging.info(f"📟 PagerDuty alert triggered for {data['app_name']}")

    def _trigger_oncall_escalation(self, alert_data):
        """Trigger additional on-call escalation for critical alerts"""
        logging.critical(f"📞 ESCALATING TO ON-CALL: {alert_data['app_name']}")
        logging.critical(f"📧 Email sent to: oncall@company.com")
        logging.critical(f"📱 SMS sent to on-call engineer")
        logging.critical(f"☎️  Phone call initiated to primary on-call")

    def _log_demo_notification(self, channel, data, template_type):
        """Log demo notification for presentation purposes"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        demo_message = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║ {channel.upper()} NOTIFICATION - {timestamp}                                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Type: {template_type.upper()}                                                ║
║ App: {data.get('app_name', 'unknown')}                                      ║
║ Severity: {data.get('severity', 'unknown').upper()}                         ║
║ Message: {data.get('message', 'No message')[:50]}...                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """
        
        print(demo_message)

    # Template methods
    def _slack_drift_template(self, data):
        return f"""🚨 *Configuration Drift Detected*
*Application:* {data['app_name']}
*Severity:* {data['severity'].upper()}
*Message:* {data['message']}
*Time:* {data['timestamp']}

*Recommended Action:* Review and remediate drift
*Dashboard:* <https://argocd.company.com/applications/{data['app_name']}|View in ArgoCD>"""

    def _slack_remediation_template(self, data):
        return f"""✅ *Drift Remediation Complete*
*Application:* {data['app_name']}
*Action:* {data['action']}
*Status:* {data['status']}
*Duration:* {data.get('duration', 'N/A')}
*Time:* {data['timestamp']}"""

    def _slack_emergency_template(self, data):
        return f"""🚨 *EMERGENCY ALERT* 🚨
*Application:* {data['app_name']}
*Alert ID:* {data.get('alert_id', 'N/A')}
*Message:* {data['message']}
*Time:* {data['timestamp']}

*IMMEDIATE ACTION REQUIRED*
*On-call team has been notified*"""

    def _email_drift_template(self, data):
        return f"""Configuration drift detected in application {data['app_name']}.
        
Severity: {data['severity']}
Message: {data['message']}
Timestamp: {data['timestamp']}

Please review the application in ArgoCD and take appropriate action."""

    def _email_remediation_template(self, data):
        return f"""Drift remediation completed for application {data['app_name']}.
        
Action: {data['action']}
Status: {data['status']}
Duration: {data.get('duration', 'N/A')}
Timestamp: {data['timestamp']}"""

    def _email_emergency_template(self, data):
        return f"""EMERGENCY ALERT - Critical drift detected in {data['app_name']}.
        
Alert ID: {data.get('alert_id', 'N/A')}
Message: {data['message']}
Timestamp: {data['timestamp']}

Immediate action required. On-call team has been notified."""

    def _get_emoji_for_severity(self, severity):
        emoji_map = {
            'low': ':information_source:',
            'medium': ':warning:',
            'high': ':exclamation:',
            'critical': ':rotating_light:'
        }
        return emoji_map.get(severity, ':question:')

