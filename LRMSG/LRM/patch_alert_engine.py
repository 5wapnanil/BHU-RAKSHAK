import os

file_path = r'backend/app/services/alert_engine.py'
with open(file_path, 'r') as f:
    code = f.read()

import_statement = '''from backend.app.services.sms_service import sms_service
from backend.app.services.contacts_service import contacts_service
import time'''

if 'from backend.app.services.sms_service' not in code:
    code = code.replace('import asyncio', 'import asyncio\n' + import_statement)

severity_func = '''
def severity_level(sev: str) -> int:
    return {"LOW": 0, "MODERATE": 1, "HIGH": 2, "CRITICAL": 3}.get(sev, 0)
'''
if 'def severity_level' not in code:
    code = code.replace('class AlertEngine:', severity_func + '\nclass AlertEngine:')

dispatch_func = '''    async def _dispatch_sms(self, alert: dict, severity: str):
        if severity not in ["HIGH", "CRITICAL"]:
            return
            
        contacts = contacts_service.get_affected_contacts(alert["latitude"], alert["longitude"])
        msg = ""
        if severity == "CRITICAL":
            msg = f"CRITICAL LANDSLIDE ALERT: Very high landslide risk ({alert['risk_probability']}%) detected near {alert['location_name']}. Move away from vulnerable slopes immediately."
        else:
            msg = f"LANDSLIDE WARNING: High landslide risk ({alert['risk_probability']}%) detected near {alert['location_name']}. Avoid vulnerable slopes. Follow local authority instructions."
            
        now = time.time()
        for c in contacts:
            cid = c["id"]
            
            if "contact_history" not in alert: alert["contact_history"] = {}
            if cid not in alert["contact_history"]: alert["contact_history"][cid] = {"last_time": 0, "last_sev": "LOW"}
            
            history = alert["contact_history"][cid]
            
            escalated = severity_level(severity) > severity_level(history["last_sev"])
            cooldown_passed = (now - history["last_time"]) > (4 * 3600)
            
            if escalated or cooldown_passed:
                success = await sms_service.send_sms(c["phone_number"], msg)
                if success:
                    history["last_time"] = now
                    history["last_sev"] = severity

    async def broadcast('''

code = code.replace('    async def broadcast(', dispatch_func)

# Hook it into new alert creation
new_alert_hook_old = '''self.alerts[alert_id] = new_alert
                self.save_alerts()
                await self.broadcast({"type": "NEW_ALERT", "alert": new_alert, "demo": demo_mode})'''
new_alert_hook_new = '''self.alerts[alert_id] = new_alert
                await self._dispatch_sms(new_alert, severity)
                self.save_alerts()
                await self.broadcast({"type": "NEW_ALERT", "alert": new_alert, "demo": demo_mode})'''

code = code.replace(new_alert_hook_old, new_alert_hook_new)

# Hook it into alert update
update_alert_hook_old = '''self.save_alerts()
                event_type = "ALERT_ESCALATED" if severity in ["CRITICAL", "HIGH"] and old_severity in ["LOW", "MODERATE"] else "ALERT_UPDATED"
                await self.broadcast({"type": event_type, "alert": alert, "demo": demo_mode})'''
update_alert_hook_new = '''await self._dispatch_sms(alert, severity)
                self.save_alerts()
                event_type = "ALERT_ESCALATED" if severity_level(severity) > severity_level(old_severity) else "ALERT_UPDATED"
                await self.broadcast({"type": event_type, "alert": alert, "demo": demo_mode})'''

code = code.replace(update_alert_hook_old, update_alert_hook_new)

with open(file_path, 'w') as f:
    f.write(code)

print("Patched alert_engine.py")
