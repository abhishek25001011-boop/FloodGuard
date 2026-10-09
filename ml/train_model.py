"""Train and evaluate the local storm-drain risk classifier."""

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import train_test_split


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT_DIR / "data" / "flood_data.csv"
MODEL_PATH = Path(__file__).resolve().with_name("model.joblib")
FEATURE_ORDER_PATH = Path(__file__).resolve().with_name("feature_order.json")
FEATURES = ["water_level_cm", "moisture_pct", "rain_detected", "rise_rate_cm_min"]
TARGET = "risk"
RANDOM_SEED = 42


def main() -> None:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH}. Run ml/generate_dataset.py first.")

    data = pd.read_csv(DATA_PATH)
    expected_columns = FEATURES + [TARGET]
    if list(data.columns) != expected_columns:
        raise ValueError(f"Dataset columns must be exactly: {expected_columns}")

    X = data[FEATURES]
    y = data[TARGET]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=RANDOM_SEED, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=300,
        random_state=RANDOM_SEED,
        class_weight="balanced",
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)
    precision, recall, f1_score, _ = precision_recall_fscore_support(
        y_test, predictions, average="weighted", zero_division=0
    )

    confusion = confusion_matrix(y_test, predictions, labels=["LOW", "MODERATE", "HIGH"])
    print("Random Forest evaluation (synthetic local drainage development data)")
    print(f"Accuracy:  {accuracy:.4f}")
    print(f"Precision: {precision:.4f} (weighted)")
    print(f"Recall:    {recall:.4f} (weighted)")
    print(f"F1-score:  {f1_score:.4f} (weighted)")
    print("\nClassification report:")
    print(classification_report(y_test, predictions, zero_division=0))
    print("Confusion matrix (rows=actual, columns=predicted; LOW, MODERATE, HIGH):")
    print(confusion)

    artifact = {
        "model": model,
        "feature_order": FEATURES,
        "target": TARGET,
        "metrics": {
            "accuracy": round(float(accuracy), 4),
            "precision_weighted": round(float(precision), 4),
            "recall_weighted": round(float(recall), 4),
            "f1_weighted": round(float(f1_score), 4),
            "evaluation_scope": "synthetic development data only",
        },
        "metadata": {
            "use_case": "local storm-drain and low-lying-area overflow risk",
            "dataset": "reproducible synthetic scenarios",
            "wetness_proxy_limitation": "moisture_pct is not rainfall intensity in mm/hour",
        },
    }
    joblib.dump(artifact, MODEL_PATH)
    FEATURE_ORDER_PATH.write_text(json.dumps(FEATURES, indent=2) + "\n", encoding="utf-8")
    print(f"\nModel saved to: {MODEL_PATH}")
    print(f"Feature order saved to: {FEATURE_ORDER_PATH}")

    examples = [
        (25, 10, False, 0.3),
        (65, 65, False, 3),
        (95, 90, True, 7),
        (55, 88, True, 8),
    ]
    print("\nSanity-test predictions:")
    for water_level, moisture, rain_detected, rise_rate in examples:
        sample = pd.DataFrame([[water_level, moisture, rain_detected, rise_rate]], columns=FEATURES)
        risk = model.predict(sample)[0]
        print(
            f"water_level_cm={water_level}, moisture_pct={moisture}, rain_detected={rain_detected}, "
            f"rise_rate_cm_min={rise_rate} -> {risk}"
        )

    print("\nLimitation: these metrics measure fit to synthetic development labels only; they are not real-world flood forecasting accuracy.")


if __name__ == "__main__":
    main()
