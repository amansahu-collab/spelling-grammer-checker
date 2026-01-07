# app/pipeline/normalize.py

def normalize_text(text: str) -> str:
    """
    STEP 1: Safe text normalization.

    Purpose:
    - Make input consistent for downstream processing
    - Preserve ALL grammar and spelling errors

    Allowed operations:
    - Strip leading/trailing whitespace
    - Replace newlines with spaces
    - Collapse multiple spaces into one

    Forbidden:
    - Any spelling correction
    - Any punctuation changes
    - Any capitalization changes
    """

    if not text:
        return ""

    # Replace newlines/tabs with space
    text = text.replace("\n", " ").replace("\t", " ")

    # Collapse multiple spaces
    text = " ".join(text.split())

    return text
