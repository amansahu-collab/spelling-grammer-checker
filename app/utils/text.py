# app/utils/text.py

def safe_lower(text: str) -> str:
    """
    Lowercase helper for internal checks only.
    NEVER use this on user-facing text.
    """
    return text.lower() if text else ""
