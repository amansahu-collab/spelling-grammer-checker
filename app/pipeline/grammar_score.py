def score_grammar(
    sentence_results: list[dict],
    sentence_count: int,
) -> int:
    """
    STEP 6: PTE-aligned grammar scoring (0–4)

    Principles:
    - Sentence-level judgement (not raw error count)
    - Structural errors dominate
    - Minor errors tolerated
    - No bonus hacks
    """

    if not sentence_results or sentence_count == 0:
        return 0

    # -------------------------------------------------
    # Severity buckets
    # -------------------------------------------------

    CRITICAL = {
        "missing_subject",
        "missing_verb",
        "fragment",
        "run_on",
    }

    MAJOR = {
        "tense_error",
        "agreement_error",
    }

    MINOR = {
        "article_error",
        "preposition_error",
        "capitalization_error",
        "conjunction_missing",
        "clause_overload",
        "whitespace_error",
    }

    # -------------------------------------------------
    # Sentence classification
    # -------------------------------------------------

    critical_sentences = 0
    major_sentences = 0
    minor_sentences = 0

    for res in sentence_results:
        has_critical = any(res.get(k, 0) > 0 for k in CRITICAL)
        has_major = any(res.get(k, 0) > 0 for k in MAJOR)
        has_minor = any(res.get(k, 0) > 0 for k in MINOR)

        if has_critical:
            critical_sentences += 1
        elif has_major:
            major_sentences += 1
        elif has_minor:
            minor_sentences += 1

    # -------------------------------------------------
    # HARD FAILS (PTE style)
    # -------------------------------------------------

    # Completely broken grammar
    if critical_sentences == sentence_count:
        return 0

    # Majority sentences structurally broken
    if critical_sentences / sentence_count >= 0.5:
        return 1

    # -------------------------------------------------
    # CORE SCORING
    # -------------------------------------------------

    # Perfect / near perfect
    if critical_sentences == 0 and major_sentences == 0:
        return 4

    # Minor issues only
    if critical_sentences == 0 and major_sentences <= 1:
        return 3

    # Multiple major errors but structure survives
    if critical_sentences == 0 and major_sentences > 1:
        return 2

    # Some critical damage but not majority
    if critical_sentences > 0:
        return 1

    return 0
