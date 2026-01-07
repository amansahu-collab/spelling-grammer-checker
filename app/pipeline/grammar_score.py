def score_grammar(
    sentence_results: list[dict],
    sentence_count: int,
) -> int:
    """
    STEP 6: Final grammar scoring math (0–4), PTE-style.
    """

    if not sentence_results:
        return 0

    # ----------------------------
    # Aggregate structural counts
    # ----------------------------
    totals = {
        "missing_subject": 0,
        "missing_verb": 0,
        "fragment": 0,
        "run_on": 0,
        "conjunction_missing": 0,
        "clause_overload": 0,
    }

    for res in sentence_results:
        for k in totals:
            totals[k] += res.get(k, 0)

    # Aggregate total errors separately
    total_errors = sum(
        res.get("total_errors", 0) for res in sentence_results
    )

    # ----------------------------
    # HARD CAPS
    # ----------------------------

    # Cap A: unintelligible
    if totals["missing_subject"] >= 1 and totals["missing_verb"] >= 1:
        return 0

    # Cap B: severe structural breakdown (single sentence)
    if (
        sentence_count == 1
        and (totals["fragment"] >= 1 or totals["run_on"] >= 1)
        and total_errors >= 6
    ):
        return 1

    # Cap C: multiple sentences, majority structurally broken
    if sentence_count >= 2:
        broken = sum(
            1
            for res in sentence_results
            if (
                res.get("fragment", 0) > 0
                or (
                    res.get("run_on", 0) > 0
                    and res.get("missing_subject", 0) > 0
                )
            )
        )
        if broken / sentence_count >= 0.5:
            return 1

    # ----------------------------
    # BASE SCORE (by total errors)
    # ----------------------------
    if total_errors <= 1:
        score = 4
    elif total_errors <= 4:
        score = 3
    elif total_errors <= 8:
        score = 2
    elif total_errors <= 12:
        score = 1
    else:
        score = 0

    # ----------------------------
    # STRUCTURAL DOWNGRADE
    # ----------------------------
    structural_penalty = False

    # Severe structure problems
    if (
        totals["fragment"] > 0
        or totals["run_on"] > 0
        or totals["missing_subject"] > 0
        or totals["missing_verb"] > 0
    ):
        structural_penalty = True

    # Clause coordination problems (penalize ONCE)
    if (
        totals["clause_overload"] > 0
        or totals["conjunction_missing"] > 0
    ):
        structural_penalty = True

    if structural_penalty:
        score -= 1

    # ----------------------------
    # CLAUSE OVERLOAD CAP (KEY FIX)
    # ----------------------------
    # A sentence with clause overload cannot score a perfect 4
    if totals["clause_overload"] > 0 and score == 4:
        score = 3

    # ----------------------------
    # STRUCTURAL BONUS
    # ----------------------------
    # Bonus only if structure is fully clean
    if (
        sentence_count == 1
        and totals["fragment"] == 0
        and totals["run_on"] == 0
        and totals["clause_overload"] == 0
        and totals["conjunction_missing"] == 0
        and total_errors <= 2
    ):
        score += 1
    
    # Clamp final score
    score = max(0, min(4, score))

    return score
