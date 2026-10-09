"""Send synthetic local storm-drain readings to FloodGuard."""

import argparse
import time
from typing import Any

import numpy as np
import requests

DEFAULT_API_URL = "http://127.0.0.1:8000/predict"
SCENARIOS = (
    "normal_drainage",
    "rising_water",
    "rapid_water_rise",
    "high_wetness_rising_water",
    "potential_storm_drain_overflow",
    # Legacy names remain accepted for existing demo scripts and API clients.
    "low",
    "moderate",
    "high",
    "rapid_rise",
)
WETNESS_DETECTION_THRESHOLD_PCT = 75.0


def _bounded_normal(rng: np.random.Generator, low: float, high: float) -> float:
    midpoint = (low + high) / 2
    return round(float(np.clip(rng.normal(midpoint, (high - low) / 6), low, high)), 2)


def generate_reading(scenario: str, step: int, rng: np.random.Generator) -> dict[str, Any]:
    """Generate the same four-field JSON contract used by the ESP8266 firmware."""
    ranges = {
        "normal_drainage": ((10, 35), (15, 55), (0, 0.8)),
        "rising_water": ((35, 75), (35, 75), (1, 4)),
        "rapid_water_rise": ((35, 85), (45, 85), (4, 9)),
        "high_wetness_rising_water": ((45, 100), (75, 100), (3, 8)),
        "potential_storm_drain_overflow": ((80, 140), (80, 100), (6, 12)),
        "low": ((10, 35), (15, 55), (0, 0.8)),
        "moderate": ((35, 75), (35, 75), (1, 4)),
        "high": ((80, 140), (80, 100), (6, 12)),
    }
    if scenario in ranges:
        level_range, wetness_range, rise_range = ranges[scenario]
        moisture = _bounded_normal(rng, *wetness_range)
        return {
            "water_level_cm": _bounded_normal(rng, *level_range),
            "moisture_pct": moisture,
            "rain_detected": moisture >= WETNESS_DETECTION_THRESHOLD_PCT,
            "rise_rate_cm_min": _bounded_normal(rng, *rise_range),
        }
    moisture = round(float(np.clip(45 + 7 * step + rng.normal(0, 3), 0, 100)), 2)
    return {
        "water_level_cm": round(float(np.clip(35 + 7 * step + rng.normal(0, 1.5), 0, 140)), 2),
        "moisture_pct": moisture,
        "rain_detected": moisture >= WETNESS_DETECTION_THRESHOLD_PCT,
        "rise_rate_cm_min": round(float(np.clip(2.5 + 0.85 * step + rng.normal(0, 0.25), 0, 12)), 2),
    }


def send_reading(reading: dict[str, Any], api_url: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        response = requests.post(api_url, json=reading, timeout=5)
    except requests.RequestException:
        return None, f"Cannot connect to FloodGuard API. Make sure FastAPI is running on {api_url.rsplit('/', 1)[0]}"
    if not response.ok:
        return None, f"FloodGuard API returned HTTP {response.status_code}: {response.text}"
    try:
        return response.json(), None
    except ValueError:
        return None, "FloodGuard API returned an invalid JSON response."


def display_result(reading: dict[str, Any], result: dict[str, Any] | None, error: str | None) -> None:
    print("-" * 40)
    print("FloodGuard Sensor Simulation")
    print("-" * 40)
    print(f"Water Level : {reading['water_level_cm']:.2f} cm")
    print(f"Wetness     : {reading['moisture_pct']:.2f}% (0 dry, 100 wet)")
    print(f"Rain/Wet    : {'DETECTED' if reading['rain_detected'] else 'NOT DETECTED'}")
    print(f"Rise Rate   : {reading['rise_rate_cm_min']:.2f} cm/min")
    print(f"API Error   : {error}" if error else f"Predicted   : {result['risk']}")
    print("-" * 40)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send simulated FloodGuard sensor data to the API.")
    parser.add_argument("--scenario", required=True, choices=SCENARIOS)
    parser.add_argument("--interval", type=float, help="Seconds between readings; omit for one reading")
    parser.add_argument("--api-url", default=DEFAULT_API_URL)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.interval is not None and args.interval <= 0:
        parser.error("--interval must be greater than zero")
    return args


def main() -> int:
    args = parse_arguments()
    rng, step = np.random.default_rng(args.seed), 0
    try:
        while True:
            reading = generate_reading(args.scenario, step, rng)
            result, error = send_reading(reading, args.api_url)
            display_result(reading, result, error)
            if args.interval is None:
                return 0 if error is None else 1
            step += 1
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nSimulation stopped.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
