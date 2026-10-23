with open('backend/app/api/endpoints/risk_zones.py', 'r') as f:
    code = f.read()

code = code.replace('from fastapi import APIRouter, Query', 'from fastapi import APIRouter, Query, BackgroundTasks')

old_def = '''def get_nearby_risk(
    lat: float = Query(..., description="User latitude"),
    lng: float = Query(..., description="User longitude"),
    radius_km: float = Query(default=150.0, description="Search radius in km"),
) -> Dict[str, Any]:'''

new_def = '''def _trigger_alerts_background(results):
    import asyncio
    async def _do_trigger():
        for z in results:
            if z["risk_probability"] >= 30.0:
                await alert_engine.evaluate_prediction(
                    location_id=f"loc_{z['lat']}_{z['lng']}",
                    location_name=z['name'], district=z['name'], state=z['state'],
                    lat=z['lat'], lng=z['lng'], probability=z['risk_probability']/100.0,
                    rainfall=z['rainfall_mm'], soil=z['soil_moisture']/100.0, slope=z['slope']
                )
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_do_trigger())
    except RuntimeError:
        asyncio.run(_do_trigger())

def get_nearby_risk(
    background_tasks: BackgroundTasks,
    lat: float = Query(..., description="User latitude"),
    lng: float = Query(..., description="User longitude"),
    radius_km: float = Query(default=150.0, description="Search radius in km"),
) -> Dict[str, Any]:'''

code = code.replace(old_def, new_def)

old_data = '''    user_zone = nearby[0] if nearby else None

    return {'''
new_data = '''    user_zone = nearby[0] if nearby else None
    background_tasks.add_task(_trigger_alerts_background, all_zones)
    return {'''

code = code.replace(old_data, new_data)

with open('backend/app/api/endpoints/risk_zones.py', 'w') as f:
    f.write(code)
print("Patched background tasks")
