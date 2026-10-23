import asyncio
import os
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.services.alert_engine import alert_engine
from backend.app.services.sms_service import sms_service
from backend.app.services.contacts_service import contacts_service

contacts_service.contacts = [
    {
        "id": "test_usr_1",
        "name": "Test Officer",
        "phone_number": "+1234567890",
        "latitude": 26.0,
        "longitude": 92.0,
        "sms_enabled": True,
        "alert_radius_km": 150.0
    }
]

async def run_tests():
    print("Running SMS Alerting Tests...")

    alert_engine.alerts.clear()

    # TEST 1-7 (Safe Mode)
    print("\n--- TEST 1: LOW PREDICTION (Safe) ---")
    await alert_engine.evaluate_prediction(
        location_id="loc_test_1", location_name="Test Area", district="Test Dist",
        state="Test State", lat=26.0, lng=92.0, probability=0.1, rainfall=0, soil=0.5, slope=20.0
    )
    print("\n--- TEST 2: MODERATE PREDICTION (Safe) ---")
    await alert_engine.evaluate_prediction(
        location_id="loc_test_1", location_name="Test Area", district="Test Dist",
        state="Test State", lat=26.0, lng=92.0, probability=0.45, rainfall=0, soil=0.5, slope=20.0
    )
    print("\n--- TEST 3: HIGH PREDICTION (Safe) ---")
    await alert_engine.evaluate_prediction(
        location_id="loc_test_1", location_name="Test Area", district="Test Dist",
        state="Test State", lat=26.0, lng=92.0, probability=0.80, rainfall=0, soil=0.5, slope=20.0
    )
    print("\n--- TEST 5: REPEATED HIGH PREDICTION (Safe) ---")
    await alert_engine.evaluate_prediction(
        location_id="loc_test_1", location_name="Test Area", district="Test Dist",
        state="Test State", lat=26.0, lng=92.0, probability=0.82, rainfall=0, soil=0.5, slope=20.0
    )
    print("\n--- TEST 7: ESCALATION HIGH -> CRITICAL (Safe) ---")
    await alert_engine.evaluate_prediction(
        location_id="loc_test_1", location_name="Test Area", district="Test Dist",
        state="Test State", lat=26.0, lng=92.0, probability=0.98, rainfall=0, soil=0.5, slope=20.0
    )
    
    # Active Tests
    sms_service.sms_enabled = True
    
    # Missing config test
    print("\n--- TEST 8: MISSING 2FACTOR KEY (Active) ---")
    sms_service.api_key = None
    await alert_engine.evaluate_prediction(
        location_id="loc_test_2", location_name="Test Area 2", district="Test Dist",
        state="Test State", lat=26.0, lng=92.0, probability=0.85, rainfall=0, soil=0.5, slope=20.0
    )
    
    sms_service.api_key = "fake_key"
    sms_service.sender_id = "LNDSLD"
    sms_service.template_name = None
    
    # API error test
    print("\n--- TEST 9: 2FACTOR API ERROR ---")
    with patch("requests.post") as mock_post:
        import requests
        mock_post.side_effect = requests.exceptions.RequestException("Connection refused")
        
        await alert_engine.evaluate_prediction(
            location_id="loc_test_3", location_name="Test Area 3", district="Test Dist",
            state="Test State", lat=26.0, lng=92.0, probability=0.88, rainfall=0, soil=0.5, slope=20.0
        )
        assert mock_post.called
    
    # 2Factor valid payload test
    print("\n--- TEST 10: 2FACTOR PAYLOAD ---")
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {"Status": "Success", "Details": "session_123"}
        mock_post.return_value = mock_response
        
        await alert_engine.evaluate_prediction(
            location_id="loc_test_4", location_name="Test Area 4", district="Test Dist",
            state="Test State", lat=26.0, lng=92.0, probability=0.95, rainfall=0, soil=0.5, slope=20.0
        )
        
        assert mock_post.called
        kwargs = mock_post.call_args.kwargs
        payload = kwargs["data"]
        print(f"Payload sent: {payload}")
        assert payload["To"] == "1234567890" # Stripped +
        assert payload["From"] == "LNDSLD"
        assert "CRITICAL LANDSLIDE ALERT" in payload["Msg"]

    print("\nTests complete. All assertions passed.")

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_tests())
