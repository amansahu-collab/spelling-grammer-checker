# app/pipeline/grammar_spacy.py

from nlp import get_nlp


def refine_with_spacy(sentence: str, errors: dict) -> dict:
    """
    STEP 4: spaCy-based structural validation.
    Reinforces and augments rule-based grammar error counts.
    """

    if not sentence:
        return errors

    doc = get_nlp()(sentence)

    # --------------------------------------------------
    # ROOT verb check (FIXED)
    # Accept VERB or AUX as valid root
    # --------------------------------------------------
    roots = [
        t for t in doc
        if t.dep_ == "ROOT" and t.pos_ in ("VERB", "AUX")
    ]

    if not roots:
        errors["missing_verb"] += 1
        errors["fragment"] += 1

    if len(roots) > 1:
        errors["run_on"] += 1

    # --------------------------------------------------
    # Subject dependency check
    # --------------------------------------------------
    has_subject = any(t.dep_ in ("nsubj", "nsubjpass") for t in doc)
    if not has_subject:
        errors["missing_subject"] += 1
        errors["fragment"] += 1

    # --------------------------------------------------
    # Verb density vs conjunctions
    # Count VERB + AUX (FIX)
    # --------------------------------------------------
    verb_count = sum(
        1 for t in doc
        if t.pos_ in ("VERB", "AUX")
    )
    conj_count = sum(1 for t in doc if t.dep_ == "cc")

    if verb_count >= 3 and conj_count == 0:
        errors["run_on"] += 1

    # --------------------------------------------------
    # Dangling subordinate clause
    # --------------------------------------------------
    has_subordinator = any(
        t.text.lower() in ("while", "although", "because", "if", "when")
        for t in doc
    )

    if has_subordinator and not roots:
        errors["fragment"] += 1

    # --------------------------------------------------
    # RECOMPUTE TOTAL (COUNTS ONLY)
    # --------------------------------------------------
    errors["total_errors"] = sum(
        v for k, v in errors.items()
        if isinstance(v, int) and k != "total_errors"
    )

    return errors
