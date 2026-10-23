import sys
import traceback

sys.path.append("c:\\Users\\bubub\\Downloads\\LRMSG\\LRM")

from backend.app.model.prediction_service import predict_complete

def run_test():
    try:
        res = predict_complete(
            rzsm_1=0.5,
            rzsm_2=0.5,
            rzsm_3=0.5,
            cumulative_rainfall_3d_mm=50.0,
            rzsm_mean=0.5,
            rzsm_range=0.1,
            rzsm_surface_deep_diff=0.0,
            rain_rzsm_interaction=25.0,
            previous_rzsm=0.4,
            previous_rzsm_2=0.4,
            previous_rzsm_3=0.4,
            previous_rainfall=20.0,
            rzsm_0_100=0.5,
            elevation_m=1000.0,
            slope_deg=10.0,
            soil_type_wrb="Cambisols"
        )
        print("SUCCESS:", res)
    except Exception as e:
        print("ERROR OCCURRED!")
        traceback.print_exc()

if __name__ == "__main__":
    run_test()
