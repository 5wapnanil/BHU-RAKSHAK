import re
with open('backend/app/api/endpoints/prediction.py', 'r') as f:
    code = f.read()

code = code.replace('from fastapi import APIRouter, HTTPException', 'from fastapi import APIRouter, HTTPException, BackgroundTasks')
code = code.replace('from backend.app.services.opentopo_service import fetch_terrain, TerrainDataError', 'from backend.app.services.opentopo_service import fetch_terrain, TerrainDataError\nfrom backend.app.services.alert_engine import alert_engine')
code = code.replace('def location_prediction(request: LocationPredictionRequest):', 'def location_prediction(request: LocationPredictionRequest, background_tasks: BackgroundTasks):')
code = code.replace('def custom_prediction(request: CustomPredictionRequest):', 'def custom_prediction(request: CustomPredictionRequest, background_tasks: BackgroundTasks):')

new_loc = '''        res = _build_response(result, features={
            "rainfall": env_data["cumulative_rainfall_3d_mm"],
            "soilMoisture": env_data["rzsm_1"],
            "slope": terrain_data["slope_deg"],
            "elevation": terrain_data["elevation_m"],
            "soilType": soil_data["soil_type_wrb"],
        })
        background_tasks.add_task(
            alert_engine.evaluate_prediction,
            location_id=f"loc_{request.latitude}_{request.longitude}",
            location_name=f"Point ({request.latitude:.2f}, {request.longitude:.2f})",
            district="Unknown",
            state="Unknown",
            lat=request.latitude,
            lng=request.longitude,
            probability=res.probability,
            rainfall=env_data["cumulative_rainfall_3d_mm"],
            soil=env_data["rzsm_1"],
            slope=terrain_data["slope_deg"],
        )
        return res'''

code = re.sub(r'        return _build_response\(result, features=\{(.*?)\}\)', new_loc, code, flags=re.DOTALL, count=1)

new_cus = '''        res = _build_response(result, features={
            "rainfall": request.rainfall,
            "soilMoisture": request.soilMoisture,
            "slope": request.slope,
            "elevation": request.elevation,
            "soilType": request.soilType,
        })
        background_tasks.add_task(
            alert_engine.evaluate_prediction,
            location_id="custom_eval_1",
            location_name="Custom Evaluation Area",
            district="Simulation District",
            state="Simulation State",
            lat=26.0,
            lng=92.0,
            probability=res.probability,
            rainfall=request.rainfall,
            soil=request.soilMoisture,
            slope=request.slope,
        )
        return res'''

code = re.sub(r'        return _build_response\(result, features=\{(.*?)\}\)', new_cus, code, flags=re.DOTALL)

with open('backend/app/api/endpoints/prediction.py', 'w') as f:
    f.write(code)
print('Done!')
