import re
from nlp import get_nlp

# ----------------------------
# Helper: clause splitter
# ----------------------------
def _split_clauses(doc):
    clauses = []
    start = 0
    for i, t in enumerate(doc):
        if t.text.lower() in ("and", "but", "or", "so", "because", "since", "while") or t.text == ",":
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
    STEP 3: Rule-based grammar error detection (ENHANCED).
    """

    errors = {
        "missing_verb": 0,
        "missing_subject": 0,
        "fragment": 0,
        "run_on": 0,
        "agreement_error": 0,
        "tense_error": 0,
        "article_error": 0,
        "preposition_error": 0,
        "capitalization_error": 0,
        "clause_overload": 0,
        "conjunction_missing": 0,

        # diagnostics
        "copula_missing": 0,
        "agreement_error_v2": 0,
        "connector_collision": 0,
        "whitespace_error": 0,

        "total_errors": 0,
    }

    # span containers
    errors["conjunction_missing_spans"] = []
    errors["article_error_spans"] = []
    errors["preposition_error_spans"] = []
    errors["capitalization_error_spans"] = []
    errors["agreement_error_spans"] = []

    errors["agreement_error_v2_spans"] = []
    errors["copula_missing_spans"] = []
    errors["connector_collision_spans"] = []
    errors["whitespace_error_spans"] = []

    if not sentence:
        return errors

    doc = get_nlp()(sentence)
    tokens = list(doc)

    # ----------------------------
    # 1. Whitespace
    # ----------------------------
    for m in re.finditer(r"\s+[,.!?]", sentence):
        errors["whitespace_error"] += 1
        errors["whitespace_error_spans"].append(m.group())

    # ----------------------------
    # 2. Capitalization (sentence start only)
    # ----------------------------
    first_token = tokens[0]
    if first_token.text[0].islower():
        errors["capitalization_error"] += 1
        errors["capitalization_error_spans"].append(
            sentence[first_token.idx:first_token.idx + len(first_token)]
        )

    # ----------------------------
    # 3. Sentence-level structure
    # ----------------------------
    has_subject = any(t.dep_ in ("nsubj", "nsubjpass") for t in tokens)
    has_verb = any(t.pos_ == "VERB" for t in tokens)

    if not has_subject:
        errors["missing_subject"] += 1
    if not has_verb:
        errors["missing_verb"] += 1
    if not has_subject and not has_verb:
        errors["fragment"] += 1

    verb_count = sum(1 for t in tokens if t.pos_ == "VERB")
    punct_count = sum(1 for t in tokens if t.text in {".", "!", "?",";"})
    if verb_count >= 2 and punct_count == 0:
        errors["run_on"] += 1

    # ----------------------------
    # 4. Clause overload
    # ----------------------------
    conjunctions = sum(
        1 for t in tokens if t.text.lower() in ("and", "but", "while", "which", "that")
    )
    if len(tokens) > 35 and conjunctions >= 3:
        errors["clause_overload"] += 1

    # ----------------------------
    # 5. Clause-level analysis
    # ----------------------------
    clauses = _split_clauses(doc)

    for cl in clauses:
        cl_tokens = list(cl)
        cl_has_subject = any(t.dep_ in ("nsubj", "nsubjpass") for t in cl_tokens)
        cl_has_verb = any(t.pos_ in ("VERB", "AUX") for t in cl_tokens)

        if cl_has_subject and not cl_has_verb:
            has_later_verb = any(
                t.pos_ in ("VERB", "AUX") and t.dep_ != "aux"
                for t in tokens
                if t.i > cl_tokens[-1].i
            )
            if not has_later_verb:
                errors["copula_missing"] += 1
                errors["copula_missing_spans"].append(cl.text)

        # agreement v2 (be-verb)
        for t in cl_tokens:
            if t.dep_ in ("nsubj", "nsubjpass"):
                verb = t.head
                if verb.pos_ in ("AUX", "VERB"):
                    if t.tag_ == "NN" and verb.text.lower() == "were":
                        errors["agreement_error_v2"] += 1
                        errors["agreement_error_v2_spans"].append(
                            sentence[t.idx:verb.idx + len(verb)]
                        )

    # ----------------------------
    # 5.5 Missing article after conjunction (NEW)
    # ----------------------------
    for i, t in enumerate(tokens[:-2]):
        if t.text.lower() in ("and", "or", "but"):
            next_tok = tokens[i + 1]
            next_next = tokens[i + 2]

            if (
                next_tok.tag_ in ("NN", "JJ")
                and next_next.tag_ == "NN"
                and not any(
                    tok.text.lower() in ("a", "an", "the")
                    for tok in tokens[max(0, i - 2): i + 1]
                )
            ):
                errors["article_error"] += 1
                span = sentence[next_tok.idx: next_next.idx + len(next_next)]
                errors["article_error_spans"].append(span)

    # ----------------------------
    # 6. Connector collision
    # ----------------------------
    for i in range(len(tokens) - 1):
        if tokens[i].text.lower() in ("and", "but") and tokens[i + 1].text.lower() in ("and", "but"):
            errors["connector_collision"] += 1
            errors["connector_collision_spans"].append(
                sentence[tokens[i].idx:tokens[i + 1].idx + len(tokens[i + 1])]
            )

    # ----------------------------
    # 7. Agreement errors
    # ----------------------------
    for t in tokens:
        if t.dep_ in ("nsubj", "nsubjpass"):
            verb = t.head

            # strict BE agreement
            if verb.pos_ == "VERB" and verb.lemma_ == "be":
                if t.tag_ in ("NN", "NNP") and verb.text.lower() == "were":
                    errors["agreement_error"] += 1
                    errors["agreement_error_spans"].append(
                        sentence[t.idx:verb.idx + len(verb)]
                    )
                if t.tag_ in ("NNS", "NNPS") and verb.text.lower() == "was":
                    errors["agreement_error"] += 1
                    errors["agreement_error_spans"].append(
                        sentence[t.idx:verb.idx + len(verb)]
                    )

            # agreement v3 (abstract noun + base verb)
            if t.tag_ == "NN" and verb.pos_ == "VERB" and verb.tag_ in ("VB", "VBP"):
                errors["agreement_error"] += 1
                errors["agreement_error_spans"].append(
                    sentence[t.idx:verb.idx + len(verb)]
                )

    # ----------------------------
    # 8. Tense heuristic
    # ----------------------------
    if re.search(r"\b(yesterday|last|ago)\b", sentence.lower()):
        if any(t.tag_ in ("VBP", "VBZ") for t in tokens):
            errors["tense_error"] += 1

    # ----------------------------
    # 9. Article misuse (a/an + plural)
    # ----------------------------
    for i, t in enumerate(tokens[:-1]):
        if t.text.lower() in ("a", "an") and tokens[i + 1].tag_ == "NNS":
            errors["article_error"] += 1
            errors["article_error_spans"].append(
                sentence[t.idx:tokens[i + 1].idx + len(tokens[i + 1])]
            )

    # ----------------------------
    # 10. Preposition misuse
    # ----------------------------
    for t in tokens:
        if t.text.lower() in ("increase", "increased", "increasing"):
            for c in t.children:
                if c.text.lower() == "on":
                    errors["preposition_error"] += 1
                    errors["preposition_error_spans"].append(
                        sentence[t.idx:c.idx + len(c)]
                    )

    # ----------------------------
    # 11. Total errors
    # ----------------------------
    errors["total_errors"] = sum(
        v for k, v in errors.items()
        if isinstance(v, int) and k != "total_errors"
    )

    return errors
