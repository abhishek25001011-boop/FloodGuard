"""Generate synthetic local storm-drain overflow scenarios for development.

The readings represent one monitored drain or low-lying area. They are not a
record of real rainfall or flood events and must not be used to estimate
real-world risk or accuracy.
"""

from pathlib import Path

import numpy as np
import pandas as pd


RANDOM_SEED = 42
SAMPLE_COUNT = 6_000
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "flood_data.csv"


def generate_dataset(sample_count: int = SAMPLE_COUNT, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """Create balanced, overlapping local drainage scenarios.

    Moisture is a calibrated wetness proxy. It is intentionally not converted
    to rainfall intensity because the analog sensor cannot measure mm/hour.
    """
    if sample_count < 3:
        raise ValueError("sample_count must be at least 3")

    rng = np.random.default_rng(seed)

    # The overlapping ranges model local drainage states, not city-wide flood
    # conditions: normal drainage, rising water, and possible overflow.
    class_count = sample_count // 3
    counts = [class_count, class_count, sample_count - (class_count * 2)]
    scenario_specs = [
        ("LOW", counts[0], 28, 14, 32, 18, 0.6, 0.5, 0, 72),
        ("MODERATE", counts[1], 62, 20, 64, 18, 2.8, 1.4, 0, 105),
        ("HIGH", counts[2], 104, 24, 86, 11, 6.2, 2.0, 1, 150),
    ]
    readings = []
    labels = []
    for label, count, level_mean, level_std, moisture_mean, moisture_std, rise_mean, rise_std, level_min, level_max in scenario_specs:
        readings.append(
            np.column_stack(
                [
                    np.clip(rng.normal(level_mean, level_std, count), level_min, level_max),
                    np.clip(rng.normal(moisture_mean, moisture_std, count), 0, 100),
                    np.clip(rng.normal(rise_mean, rise_std, count), 0, 12),
                ]
            )
        )
        labels.extend([label] * count)

    values = np.vstack(readings)
    order = rng.permutation(sample_count)
    water_level = values[order, 0]
    moisture = values[order, 1]
    rise_rate = values[order, 2]
    risk = np.asarray(labels, dtype=object)[order]
    # This flag is a wetness threshold and must stay consistent with moisture.
    rain_detected = moisture >= 75.0

    return pd.DataFrame(
        {
            "water_level_cm": water_level.round(2),
            "moisture_pct": moisture.round(2),
            "rain_detected": rain_detected,
            "rise_rate_cm_min": rise_rate.round(3),
            "risk": risk,
        }
    )


def main() -> None:
    dataset = generate_dataset()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(OUTPUT_PATH, index=False)

    print(f"Synthetic development dataset saved to: {OUTPUT_PATH}")
    print(f"Rows: {len(dataset)}")
    print("Columns:", ", ".join(dataset.columns))
    print("Class distribution:")
    print(dataset["risk"].value_counts().sort_index().to_string())
    print("\nDisclaimer: this synthetic dataset is for development only and does not represent real-world flood probability.")


if __name__ == "__main__":
    main()
