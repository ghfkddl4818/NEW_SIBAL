import pandas as pd
import json
from pathlib import Path
from collections import Counter
import re

def normalize_reviews(input_dir: str, output_path: str, logger):
    review_files = list(Path(input_dir).glob('*.csv')) + list(Path(input_dir).glob('*.xlsx'))
    if not review_files:
        logger.warning(f"No review files found in {input_dir}")
        return None

    # For this MVP, we'll just use the first file found.
    filepath = review_files[0]
    if filepath.suffix == '.csv':
        df = pd.read_csv(filepath)
    else:
        df = pd.read_excel(filepath)

    # Basic keyword extraction (top 10)
    all_text = ' '.join(df.iloc[:, 0].astype(str).tolist()) # Assuming review text is in the first column
    words = re.findall(r'[\uac00-\ud7a3a-zA-Z]+', all_text.lower())
    keywords = [{ "term": term, "count": count } for term, count in Counter(words).most_common(10)]

    # Dummy data for other fields
    normalized_data = {
        "stats": {
            "total_reviews": len(df),
            "rating_avg": None, # Placeholder
            "recent_ratio_30d": None # Placeholder
        },
        "signals": {
            "demand": [], # Placeholder
            "friction": [], # Placeholder
            "keywords_top": keywords
        },
        "quotes": {
            "positive": [], # Placeholder
            "negative": [] # Placeholder
        }
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(normalized_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Normalized reviews written to {output_path}")
    return normalized_data
