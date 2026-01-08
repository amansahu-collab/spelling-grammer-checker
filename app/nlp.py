import threading
import spacy

_nlp = None
_lock = threading.Lock()


def get_nlp():
    """
    Returns the shared spaCy NLP model instance.
    Loads 'en_core_web_sm' lazily on first call.
    Thread-safe.
    """
    global _nlp
    if _nlp is None:
        with _lock:
            if _nlp is None:  # Double-check locking
                _nlp = spacy.load("en_core_web_sm")
    return _nlp