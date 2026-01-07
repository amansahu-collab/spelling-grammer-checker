# app/pipeline/spelling.py

import re
from spellchecker import SpellChecker

_spell = SpellChecker()


def evaluate_spelling(text: str) -> dict:
    """
    Spelling evaluation (PTE-style).

    - Tokenize words
    - Count misspellings
    - Return misspelled words
    - Compute spelling score (0–4)
    """

    if not text:
        return {
            "total_words": 0,
            "misspelled_count": 0,
            "misspelled_words": [],
            "spelling_score": 4,
        }

    # Extract alphabetic tokens only
    words = re.findall(r"\b[a-zA-Z]+\b", text)
    lower_words = [w.lower() for w in words]
 

    if not lower_words:
        return {
            "total_words": 0,
            "misspelled_count": 0,
            "misspelled_words": [],
            "spelling_score": 4,
        }

    misspelled = _spell.unknown(lower_words)

    misspelled_words = sorted(misspelled)
    misspelled_count = len(misspelled_words)
    total_words = len(lower_words)

    # PTE-style score mapping
    if misspelled_count == 0:
        score = 4
    elif misspelled_count <= 2:
        score = 3
    elif misspelled_count <= 5:
        score = 2
    elif misspelled_count <= 9:
        score = 1
    else:
        score = 0

    return {
        "total_words": total_words,
        "misspelled_count": misspelled_count,
        "misspelled_words": misspelled_words,
        "spelling_score": score,
    }
