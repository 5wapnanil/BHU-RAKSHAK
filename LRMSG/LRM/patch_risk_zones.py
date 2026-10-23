with open('backend/app/api/endpoints/risk_zones.py', 'r') as f:
    code = f.read()

import_statement = '''from backend.app.services.alert_engine import alert_engine
import asyncio'''
code = code.replace('from fastapi import APIRouter, Query', 'from fastapi import APIRouter, Query\n' + import_statement)

patch = '''    data = {
        "zones": results,
'''
new_patch = '''    try:
        loop = asyncio.get_running_loop()
        for z in results:
            if z["risk_probability"] >= 30.0:  # Only trigger if MODERATE or above
                loop.create_task(alert_engine.evaluate_prediction(
                    location_id=f"loc_{z['lat']}_{z['lng']}",
                    location_name=z['name'],
                    district=z['name'],
                    state=z['state'],
                    lat=z['lat'],
                    lng=z['lng'],
                    probability=z['risk_probability'] / 100.0,
                    rainfall=z['rainfall_mm'],
                    soil=z['soil_moisture'] / 100.0,
                    slope=z['slope']
                ))
    except Exception as e:
        print("Could not trigger alerts", e)

    data = {
        "zones": results,
'''
code = code.replace(patch, new_patch)

with open('backend/app/api/endpoints/risk_zones.py', 'w') as f:
    f.write(code)
print("Patched risk_zones.py")
