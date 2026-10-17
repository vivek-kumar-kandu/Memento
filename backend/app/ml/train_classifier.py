import json
from pathlib import Path
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline

from app.ml.dataset import DATASET, INTENT_CLASSES

RANDOM_SEED = 42
MODEL_OUTPUT_PATH = Path(__file__).resolve().parent / "intent_classifier.joblib"
METRICS_OUTPUT_PATH = Path(__file__).resolve().parent / "evaluation_report.json"


def train_and_evaluate():
    texts = [item["text"] for item in DATASET]
    labels = [item["intent"] for item in DATASET]
    groups = [item["group_id"] for item in DATASET]

    total_samples = len(texts)
    unique_groups = len(set(groups))
    print(f"Total dataset size: {total_samples} samples across {unique_groups} grouped phrase families.")

    # Group-aware train/test split to prevent data leakage across paraphrases
    gss = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=RANDOM_SEED)
    train_idx, test_idx = next(gss.split(texts, labels, groups=groups))

    X_train = [texts[i] for i in train_idx]
    y_train = [labels[i] for i in train_idx]
    X_test = [texts[i] for i in test_idx]
    y_test = [labels[i] for i in test_idx]

    print(f"Train set: {len(X_train)} samples | Held-out test set: {len(X_test)} samples")

    # Lightweight TF-IDF character + word n-gram pipeline robust to Hindi/Hinglish spelling variants
    pipeline = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(2, 5),
                    analyzer="char_wb",
                    sublinear_tf=True,
                    min_df=1,
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    C=2.0,
                    max_iter=1000,
                    random_state=RANDOM_SEED,
                    class_weight="balanced",
                ),
            ),
        ]
    )

    # Train on training partition
    pipeline.fit(X_train, y_train)

    # Evaluate on strictly held-out test partition
    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    report_dict = classification_report(y_test, y_pred, labels=INTENT_CLASSES, zero_division=0, output_dict=True)
    report_text = classification_report(y_test, y_pred, labels=INTENT_CLASSES, zero_division=0)

    print("\n--- HELD-OUT EVALUATION REPORT ---")
    print(report_text)
    print(f"Overall Held-out Accuracy: {acc:.4f}")

    # Retrain on full dataset for maximum generalization in production, while preserving evaluated metrics
    full_pipeline = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(2, 5),
                    analyzer="char_wb",
                    sublinear_tf=True,
                    min_df=1,
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    C=2.0,
                    max_iter=1000,
                    random_state=RANDOM_SEED,
                    class_weight="balanced",
                ),
            ),
        ]
    )
    full_pipeline.fit(texts, labels)

    # Save artifact
    joblib.dump(full_pipeline, MODEL_OUTPUT_PATH)
    print(f"\nTrained intent pipeline saved to: {MODEL_OUTPUT_PATH}")

    # Save evaluation metrics
    metrics = {
        "random_seed": RANDOM_SEED,
        "dataset_total_samples": total_samples,
        "dataset_groups": unique_groups,
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "held_out_accuracy": float(acc),
        "held_out_classification_report": report_dict,
        "intents": INTENT_CLASSES,
        "model_pipeline": "TfidfVectorizer(char_wb, 2-5) + LogisticRegression(balanced)",
        "limitations": (
            "Model is an intent router trained on domain-specific emergency utterances in English, "
            "Devanagari Hindi, and Hinglish. It does NOT diagnose venom type, identify snake species, "
            "or assess clinical severity."
        ),
    }
    with open(METRICS_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(f"Metrics saved to: {METRICS_OUTPUT_PATH}")

    return metrics


if __name__ == "__main__":
    train_and_evaluate()
