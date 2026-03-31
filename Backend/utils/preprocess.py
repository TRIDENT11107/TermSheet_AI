import pandas as pd
import re
import nltk
from nltk.corpus import stopwords
from pathlib import Path

# Download NLTK stopwords if not already present
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

stop_words = set(stopwords.words('english'))

def clean_text(text):
    """Remove special characters, lowercase, and strip whitespace."""
    if isinstance(text, str):
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s]', '', text)
        text = text.lower().strip()
        # Remove stopwords
        tokens = [word for word in text.split() if word not in stop_words]
        return " ".join(tokens)
    return ""

if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    input_path = project_root / "Datasets" / "Term-Sheet.csv"
    output_path = project_root / "Datasets" / "term_sheet_preprocessed.csv"

    # Process Term-Sheet.csv
    with open(input_path, "r", encoding="utf-8") as source_file:
        lines = [line.strip().strip('"') for line in source_file if line.strip().strip('"')]

    # Clean the lines
    cleaned_lines = [clean_text(line) for line in lines if len(line.strip()) > 10]

    # Do not fabricate labels. Keep label empty so bad training data is not created silently.
    df = pd.DataFrame({"text": cleaned_lines, "label": pd.NA})
    df.to_csv(output_path, index=False)
    print(f"Preprocessing complete. Saved to {output_path}")
    print(
        "Labels were left empty intentionally. Populate the 'label' column with real "
        "values (for example 'valid'/'invalid') before training."
    )
