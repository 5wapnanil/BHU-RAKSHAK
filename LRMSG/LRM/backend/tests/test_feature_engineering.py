import math

from backend.app.services.feature_engineering import (
    calculate_rzsm_mean,
    calculate_rzsm_range,
    calculate_surface_deep_difference,
    calculate_rain_rzsm_interaction,
    calculate_rzsm_0_100,
)


def test_rzsm_mean():
    assert math.isclose(calculate_rzsm_mean(0.10, 0.20, 0.30), 0.20)

def test_rzsm_range():
    assert math.isclose(calculate_rzsm_range(0.10, 0.30, 0.20), 0.20)

def test_surface_deep_difference():
    assert math.isclose(calculate_surface_deep_difference(0.10, 0.30), -0.20)

def test_rain_rzsm_interaction():
    assert math.isclose(calculate_rain_rzsm_interaction(100.0, 0.20), 20.0)


def test_rzsm_0_100():

    value = calculate_rzsm_0_100(
        0.10,
        0.20,
        0.30,
    )

    expected = (
        7 * 0.10
        + 21 * 0.20
        + 72 * 0.30
    ) / 100

    assert abs(value - expected) < 1e-12
