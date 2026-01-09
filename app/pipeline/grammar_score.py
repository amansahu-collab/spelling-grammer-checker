def score_grammar(
    sentence_results: list[dict],
    sentence_count: int,
) -> int:
    """
    STEP 6: PTE-aligned grammar scoring (0–4)

    Philosophy:
    - Sentence quality > raw error count
    - Structural breakdown dominates
    - Major grammar errors reduce score sharply
    - Minor errors tolerated
    """

    if not sentence_results or sentence_count == 0:
        return 0

    # -------------------------------------------------
    # Error severity buckets (UPDATED to match pipeline)
    # -------------------------------------------------

    CRITICAL = {
        "missing_subject",
        "missing_verb",
        "fragment",
        "run_on",
    }

    MAJOR = {
        "aux_verb_error",
        "tense_error",
        "comparison_error",
        "pronoun_agreement_error",
    }

    MINOR = {
        "article_error",
        "capitalization_error",
        "conjunction_missing",
        "clause_overload",
        "whitespace_error",
    }

    # -------------------------------------------------
    # Sentence-level classification
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
    # HARD FAILS (PTE behaviour)
    # -------------------------------------------------

    # Completely broken grammar
    if critical_sentences == sentence_count:
        return 0

    # Majority sentences structurally broken
    if critical_sentences / sentence_count >= 0.5:
        return 1

    # -------------------------------------------------
    # CORE SCORING LOGIC
    # -------------------------------------------------

    # ✅ Score 4: Meaning clear, grammar strong
    if critical_sentences == 0 and major_sentences == 0:
        return 4

    # ✅ Score 3: Meaning clear, some grammar damage
    if critical_sentences == 0 and major_sentences == 1:
        return 3

    # ✅ Score 2: Meaning mostly clear, frequent grammar errors
    if critical_sentences == 0 and major_sentences > 1:
        return 2

    # ✅ Score 1: Meaning partially obscured
    if critical_sentences > 0:
        return 1

    return 0
