from final_calibration import (
    calibrate_final_probability,
    calibrated_final_result
)


# ============================================================
# TEST VALUES
# ============================================================

test_values = [
    0.01,
    0.10,
    0.20,
    0.30,
    0.40,
    0.50,
    0.60,
    0.6351159552557684,
    0.70,
    0.80,
    0.90,
    0.95,
    0.99,
    0.999
]


print("=" * 75)
print("FINAL DECISION-LAYER CALIBRATION TEST")
print("=" * 75)

for raw in test_values:

    calibrated = calibrate_final_probability(raw)

    print(
        f"Raw Final: {raw:.10f}"
        f" -> Calibrated Final: {calibrated:.10f}"
    )


# ============================================================
# KOLKATA VERIFICATION
# ============================================================

print("=" * 75)
print("KOLKATA VERIFICATION")
print("=" * 75)

kolkata_raw_final = 0.6351159552557684

result = calibrated_final_result(
    kolkata_raw_final
)

print(result)


print("=" * 75)
print("EXPECTED RESULT")
print("=" * 75)

print("Raw Final       : 63.5116%")
print("Calibrated Final: approximately 50.97%")
