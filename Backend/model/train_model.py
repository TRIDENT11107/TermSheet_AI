import argparse
import json
import pickle
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.svm import LinearSVC


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BOOTSTRAP_DATASET = PROJECT_ROOT / "Datasets" / "term_sheet_bootstrap_labeled.csv"
DEFAULT_FALLBACK_DATASET = PROJECT_ROOT / "Datasets" / "term_sheet_preprocessed.csv"
MODEL_DIR = PROJECT_ROOT / "Backend" / "model"
METRICS_PATH = MODEL_DIR / "metrics.json"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Train and evaluate TermSheet AI classifier."
    )
    parser.add_argument(
        "--dataset",
        default=None,
        help=(
            "Path to CSV dataset with columns: text,label. "
            "Defaults to term_sheet_bootstrap_labeled.csv if present."
        ),
    )
    parser.add_argument(
        "--allow-suspicious-labels",
        action="store_true",
        help="Allow training even if labels look alternating/synthetic.",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Holdout test split ratio (default: 0.2).",
    )
    return parser.parse_args()


def resolve_dataset_path(user_value: str | None) -> Path:
    if user_value:
        candidate = Path(user_value)
        return candidate if candidate.is_absolute() else (PROJECT_ROOT / candidate)
    if DEFAULT_BOOTSTRAP_DATASET.exists():
        return DEFAULT_BOOTSTRAP_DATASET
    return DEFAULT_FALLBACK_DATASET


def load_dataset(path: Path, allow_suspicious_labels: bool) -> tuple[pd.DataFrame, dict]:
    df = pd.read_csv(path)
    print(f"Loaded {len(df)} rows from {path}")
    print(f"Columns: {df.columns.tolist()}")

    if "text" not in df.columns or "label" not in df.columns:
        raise ValueError("Dataset must contain 'text' and 'label' columns")

    before = len(df)
    df = df.dropna(subset=["text", "label"]).copy()
    df["text"] = df["text"].astype(str).str.strip()
    df = df[df["text"] != ""]
    after = len(df)
    dropped = before - after
    print(f"Rows dropped during cleanup: {dropped}")
    print(f"Rows remaining: {after}")

    if after < 20:
        raise ValueError("Not enough usable rows after cleanup.")

    label_counts = df["label"].value_counts()
    print("Label distribution:")
    print(label_counts.to_string())
    if label_counts.shape[0] < 2:
        raise ValueError("Need at least 2 classes to train.")

    label_warning = None
    suspicious_pattern = False
    labels = df["label"].tolist()
    if len(labels) > 1:
        flips = sum(1 for i in range(1, len(labels)) if labels[i] != labels[i - 1])
        flip_ratio = flips / (len(labels) - 1)
        if flip_ratio > 0.95:
            suspicious_pattern = True
            label_warning = (
                "WARNING: Labels appear nearly alternating by row order. "
                "This pattern usually indicates synthetic or corrupted labels."
            )
            print(label_warning)
            if not allow_suspicious_labels:
                raise ValueError(
                    "Suspicious alternating labels detected. "
                    "Use a trusted labeled dataset or pass --allow-suspicious-labels."
                )

    metadata = {
        "rows_after_cleanup": int(len(df)),
        "label_warning": label_warning,
        "suspicious_label_pattern": suspicious_pattern,
    }
    return df, metadata


def build_candidates():
    return [
        {
            "name": "logreg_baseline",
            "vectorizer": TfidfVectorizer(max_features=1_000),
            "model": LogisticRegression(max_iter=2_000, random_state=42),
        },
        {
            "name": "logreg_tuned",
            "vectorizer": TfidfVectorizer(
                max_features=15_000,
                ngram_range=(1, 2),
                sublinear_tf=True,
                min_df=1,
            ),
            "model": LogisticRegression(
                max_iter=5_000, C=2.0, class_weight="balanced", random_state=42
            ),
        },
        {
            "name": "linear_svc_word",
            "vectorizer": TfidfVectorizer(
                max_features=20_000,
                ngram_range=(1, 3),
                sublinear_tf=True,
                min_df=1,
            ),
            "model": LinearSVC(C=1.0, class_weight="balanced", random_state=42),
        },
        {
            "name": "sgd_modified_huber",
            "vectorizer": TfidfVectorizer(
                max_features=15_000,
                ngram_range=(1, 2),
                sublinear_tf=True,
                min_df=1,
            ),
            "model": SGDClassifier(
                loss="modified_huber",
                alpha=1e-5,
                random_state=42,
                max_iter=2_000,
                tol=1e-4,
            ),
        },
        {
            "name": "linear_svc_char",
            "vectorizer": TfidfVectorizer(
                analyzer="char_wb",
                ngram_range=(3, 5),
                sublinear_tf=True,
                min_df=1,
                max_features=40_000,
            ),
            "model": LinearSVC(C=1.0, class_weight="balanced", random_state=42),
        },
    ]


def main() -> None:
    args = parse_args()
    dataset_path = resolve_dataset_path(args.dataset)
    df, dataset_meta = load_dataset(
        dataset_path, allow_suspicious_labels=args.allow_suspicious_labels
    )

    X = df["text"]
    y = df["label"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_size, random_state=42, stratify=y
    )

    candidates = build_candidates()
    best = None
    results = []

    for candidate in candidates:
        name = candidate["name"]
        vectorizer = candidate["vectorizer"]
        model = candidate["model"]

        X_train_vec = vectorizer.fit_transform(X_train)
        X_test_vec = vectorizer.transform(X_test)
        model.fit(X_train_vec, y_train)
        y_pred = model.predict(X_test_vec)

        accuracy = accuracy_score(y_test, y_pred)
        report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
        macro_f1 = report["macro avg"]["f1-score"]
        results.append({"name": name, "accuracy": accuracy, "macro_f1": macro_f1})
        print(f"{name}: accuracy={accuracy:.4f}, macro_f1={macro_f1:.4f}")

        score_key = (accuracy, macro_f1)
        if best is None or score_key > best["score_key"]:
            best = {
                "name": name,
                "vectorizer": vectorizer,
                "model": model,
                "y_pred": y_pred,
                "accuracy": accuracy,
                "report": report,
                "score_key": score_key,
            }

    if best is None:
        raise RuntimeError("No candidate model was trained.")

    print("\nBest model:", best["name"])
    print(f"Best accuracy: {best['accuracy']:.4f}")
    print(classification_report(y_test, best["y_pred"], zero_division=0))

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    with open(MODEL_DIR / "model.pkl", "wb") as model_file:
        pickle.dump(best["model"], model_file)
    with open(MODEL_DIR / "vectorizer.pkl", "wb") as vectorizer_file:
        pickle.dump(best["vectorizer"], vectorizer_file)

    metrics = {
        "dataset_path": str(dataset_path),
        "rows_used": int(len(df)),
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "suspicious_label_pattern": dataset_meta["suspicious_label_pattern"],
        "label_warning": dataset_meta["label_warning"],
        "evaluation_note": (
            "Bootstrap dataset was used. Holdout accuracy can be optimistic; "
            "validate with real externally labeled term sheets."
            if dataset_path.name == "term_sheet_bootstrap_labeled.csv"
            else None
        ),
        "best_model": best["name"],
        "best_accuracy": best["accuracy"],
        "candidate_results": results,
    }
    with open(METRICS_PATH, "w", encoding="utf-8") as metrics_file:
        json.dump(metrics, metrics_file, indent=2)

    print(f"Saved model, vectorizer, and metrics in {MODEL_DIR}")


if __name__ == "__main__":
    main()
