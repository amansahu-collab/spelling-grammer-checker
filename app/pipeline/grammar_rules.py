import re
from nlp import get_nlp

# ----------------------------
# Helper: clause splitter
# ----------------------------
def _split_clauses(doc):
    clauses = []
    start = 0
    for i, t in enumerate(doc):
        if t.text.lower() in (
            "and", "but", "or", "so", "because", "since", "while"
        ) or t.text == ",":
            span = doc[start:i]
            if span.text.strip():
                clauses.append(span)
            start = i + 1
    if start < len(doc):
        span = doc[start:]
        if span.text.strip():
            clauses.append(span)
    return clauses


def analyze_grammar_rules(sentence: str) -> dict:
    """
    STEP 3: Rule-based grammar error detection (ROBUST, PTE-aligned).
    """

    errors = {
        # core structure
        "missing_verb": 0,
        "missing_subject": 0,
        "fragment": 0,
        "run_on": 0,

        # grammar
        "aux_verb_error": 0,
        "tense_error": 0,
        "article_error": 0,
        "capitalization_error": 0,
        "comparison_error": 0,
        "pronoun_agreement_error": 0,

        # advanced
        "clause_overload": 0,
        "conjunction_missing": 0,
        "whitespace_error": 0,

        "total_errors": 0,
    }

    # ----------------------------
    # Span containers (LLM-safe)
    # ----------------------------
    for k in list(errors.keys()):
        if k != "total_errors":
            errors[f"{k}_spans"] = []

    if not sentence:
        return errors

    doc = get_nlp()(sentence)
    tokens = list(doc)

    # ----------------------------
    # 1. Whitespace issues
    # ----------------------------
    for m in re.finditer(r"\s+[,.!?]", sentence):
        errors["whitespace_error"] += 1
        errors["whitespace_error_spans"].append(m.group())

    # ----------------------------
    # 2. Capitalization (sentence start)
    # ----------------------------
    if tokens and tokens[0].text[0].islower():
        errors["capitalization_error"] += 1
        errors["capitalization_error_spans"].append(tokens[0].text)

    # ----------------------------
    # 3. Sentence structure
    # ----------------------------
    has_subject = any(t.dep_ in ("nsubj", "nsubjpass") for t in tokens)
    has_verb = any(t.pos_ in ("VERB", "AUX") for t in tokens)

    if not has_subject:
        errors["missing_subject"] += 1
        errors["missing_subject_spans"].append(sentence)

    if not has_verb:
        errors["missing_verb"] += 1
        errors["missing_verb_spans"].append(sentence)

    if not has_subject and not has_verb:
        errors["fragment"] += 1
        errors["fragment_spans"].append(sentence)

    # ----------------------------
    # 4. Aux + base verb agreement
    # doesn't has / did went / does not eats
    # ----------------------------
    for i, t in enumerate(tokens):
        if t.lemma_ == "do" and t.pos_ == "AUX":
            j = i + 1
            while j < len(tokens) and tokens[j].pos_ == "PART":
                j += 1
            if j < len(tokens):
                verb = tokens[j]
                if verb.tag_ != "VB":
                    span = sentence[t.idx : verb.idx + len(verb)]
                    errors["aux_verb_error"] += 1
                    errors["aux_verb_error_spans"].append(span)

    # ----------------------------
    # 5. Missing article before singular count noun
    # ----------------------------
    MASS_NOUNS = {"oxygen", "sodium", "water", "air", "information"}
    ZERO_ARTICLE_PLACES = {
        "school", "college", "university",
        "bed", "work", "church", "hospital", "home"
    }

    for t in tokens:
        if t.tag_ == "NN" and t.pos_ != "PROPN" and t.text.islower():
            if t.text.lower() in MASS_NOUNS or t.text.lower() in ZERO_ARTICLE_PLACES:
                continue

            has_det = any(c.dep_.startswith("det") for c in t.children) or any(
                any(c.dep_.startswith("det") for c in anc.children)
                for anc in t.ancestors
            )

            if not has_det and t.dep_ in ("dobj", "pobj", "attr"):
                errors["article_error"] += 1
                errors["article_error_spans"].append(t.text)

    # ----------------------------
    # 6. Comparative vs Superlative misuse
    # the smaller planet → should be smallest
    # ----------------------------
    for i, t in enumerate(tokens):
        if (
            t.tag_ == "JJR"
            and i > 0
            and tokens[i - 1].text.lower() == "the"
            and t.head.tag_ == "NN"
        ):
            errors["comparison_error"] += 1
            errors["comparison_error_spans"].append(t.text)

    # ----------------------------
    # 7. Pronoun agreement (singular non-human)
    # their atmosphere → its atmosphere
    # ----------------------------
    for i, t in enumerate(tokens):
        if t.text.lower() == "their":
            for prev in reversed(tokens[:i]):
                if prev.tag_ == "NN" and prev.ent_type_ != "PERSON":
                    errors["pronoun_agreement_error"] += 1
                    errors["pronoun_agreement_error_spans"].append(t.text)
                    break

    # ----------------------------
    # 8. Tense heuristic
    # yesterday / last / ago + present verb
    # ----------------------------
    if re.search(r"\b(yesterday|last|ago)\b", sentence.lower()):
        for t in tokens:
            if t.pos_ == "VERB" and t.tag_ in ("VB", "VBP", "VBZ"):
                errors["tense_error"] += 1
                errors["tense_error_spans"].append(
                    sentence[t.idx : t.idx + len(t)]
                )
                break

    # ----------------------------
    # 9. Clause overload
    # ----------------------------
    if len(tokens) > 35:
        conj_count = sum(
            1 for t in tokens if t.text.lower() in ("and", "but", "which", "that")
        )
        if conj_count >= 3:
            errors["clause_overload"] += 1
            errors["clause_overload_spans"].append(sentence)

    # ----------------------------
    # 10. Total errors
    # ----------------------------
    errors["total_errors"] = sum(
        v for k, v in errors.items()
        if isinstance(v, int) and k != "total_errors"
    )

    return errors
