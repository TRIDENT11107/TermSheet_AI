import re
from pathlib import Path
from typing import Iterable, List

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASETS_DIR = PROJECT_ROOT / "Datasets"
OUTPUT_PATH = DATASETS_DIR / "term_sheet_bootstrap_labeled.csv"


CORE_KEYWORDS = [
    "term sheet",
    "issuer",
    "investor",
    "investment amount",
    "securities offered",
    "valuation",
    "price per share",
    "liquidation preference",
    "board",
    "protective provisions",
    "registration rights",
    "maturity",
    "governing law",
]


def normalize_text(text: str) -> str:
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def read_term_sheet_lines(path: Path) -> List[str]:
    lines: List[str] = []
    with path.open("r", encoding="utf-8", errors="ignore") as source:
        for raw in source:
            value = normalize_text(raw.strip().strip('"'))
            if value:
                lines.append(value)
    return lines


def split_paragraphs(lines: Iterable[str]) -> List[str]:
    paragraphs: List[str] = []
    buffer: List[str] = []
    for line in lines:
        if line:
            buffer.append(line)
        elif buffer:
            paragraphs.append(normalize_text(" ".join(buffer)))
            buffer = []
    if buffer:
        paragraphs.append(normalize_text(" ".join(buffer)))
    return paragraphs


def keyword_hits(text: str) -> int:
    lowered = text.lower()
    return sum(1 for key in CORE_KEYWORDS if key in lowered)


def build_positive_samples(lines: List[str]) -> List[str]:
    positives: List[str] = []

    # Sliding windows over the raw term sheet text.
    for window_size in (4, 6, 8, 10):
        for i in range(0, max(0, len(lines) - window_size + 1), 2):
            chunk = normalize_text(" ".join(lines[i : i + window_size]))
            if len(chunk) < 120:
                continue
            if keyword_hits(chunk) >= 2:
                positives.append(chunk)

    # Paragraph blocks.
    for paragraph in split_paragraphs(lines):
        if len(paragraph) >= 120 and keyword_hits(paragraph) >= 2:
            positives.append(paragraph)

    # Deterministic augmentations for modest variety.
    augmented: List[str] = []
    for text in positives:
        a = re.sub(r"\$\s?\d[\d,]*(\.\d+)?", "$5,000,000", text)
        a = re.sub(
            r"\b(october|november|december|january|february)\s+\d{1,2},\s+\d{4}\b",
            "January 15, 2026",
            a,
            flags=re.IGNORECASE,
        )
        b = re.sub(r"\blevel 8 systems, inc\.\b", "Acme Holdings, Inc.", text, flags=re.IGNORECASE)
        c = re.sub(r"\bissuer\b", "issuer", text, flags=re.IGNORECASE).upper()
        augmented.extend([normalize_text(a), normalize_text(b), normalize_text(c)])

    positives.extend(augmented)
    positives = [value for value in positives if len(value) >= 120]
    positives = list(dict.fromkeys(positives))
    return positives


def build_negative_from_financial_csvs() -> List[str]:
    negatives: List[str] = []
    for csv_path in sorted(DATASETS_DIR.glob("*_final.csv")):
        try:
            frame = pd.read_csv(csv_path, dtype=str).fillna("")
        except Exception:
            continue

        for _, row in frame.iterrows():
            values = [str(v).strip() for v in row.tolist()[:12] if str(v).strip()]
            if len(values) < 3:
                continue
            text = normalize_text(" ".join(values))
            if len(text) < 40:
                continue
            negatives.append(text)

    return list(dict.fromkeys(negatives))


def build_hard_negatives(positives: List[str]) -> List[str]:
    hard_negatives: List[str] = []
    replacements = {
        r"\bissuer\b": "topic",
        r"\binvestor(s)?\b": "participants",
        r"\binvestment amount\b": "example amount",
        r"\bsecurities offered\b": "sample attributes",
        r"\bliquidation preference\b": "priority note",
        r"\bboard of directors\b": "team board",
        r"\bgoverning law\b": "region",
        r"\bterm sheet\b": "draft note",
    }
    for text in positives:
        changed = text
        for pattern, repl in replacements.items():
            changed = re.sub(pattern, repl, changed, flags=re.IGNORECASE)
        changed = f"Sample only not legally binding {changed}"
        changed = re.sub(r"\$\s?\d[\d,]*(\.\d+)?", "$123", changed)
        changed = normalize_text(changed)
        if changed and changed != text:
            hard_negatives.append(changed)

    generic = [
        "This is a fake sample document for demo only. No legal agreement, no issuer, no investors, no enforceable terms.",
        "Draft placeholder lorem ipsum for testing pipeline quality only. Contains random values and no valid financing terms.",
        "Generated mock summary with arbitrary numbers, no signatures, no legal clauses, and no transaction commitments.",
    ]
    hard_negatives.extend(generic)
    hard_negatives = [value for value in hard_negatives if len(value) >= 80]
    return list(dict.fromkeys(hard_negatives))


def main() -> None:
    raw_path = DATASETS_DIR / "Term-Sheet.csv"
    lines = read_term_sheet_lines(raw_path)

    positives = build_positive_samples(lines)
    financial_negatives = build_negative_from_financial_csvs()
    hard_negatives = build_hard_negatives(positives)
    negatives = list(dict.fromkeys(financial_negatives + hard_negatives))

    # Keep balanced classes.
    target = min(len(positives), len(negatives))
    positives = positives[:target]
    negatives = negatives[:target]

    rows = (
        [{"text": text, "label": "valid"} for text in positives]
        + [{"text": text, "label": "invalid"} for text in negatives]
    )
    dataset = pd.DataFrame(rows).sample(frac=1.0, random_state=42).reset_index(drop=True)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(OUTPUT_PATH, index=False)

    print(f"Saved bootstrap dataset: {OUTPUT_PATH}")
    print(f"Rows: {len(dataset)}")
    print(dataset["label"].value_counts().to_string())


if __name__ == "__main__":
    main()
