import spacy
import re

_nlp = spacy.load("en_core_web_sm")


def analyze_usage_clarity(sentence: str) -> dict:
    """
    Usage / clarity diagnostics (NON-GRAMMAR).
    - No scoring
    - No penalties
    - Heuristic only
    """

    issues = []

    if not sentence:
        return {"issues": []}

    doc = _nlp(sentence)
    tokens = list(doc)

    # ----------------------------
    # 1. Generic tense preference
    # ----------------------------
    # plural subject + past BE + adjective (no time marker)
    time_markers = re.search(r"\b(yesterday|last|ago|previous)\b", sentence.lower())

    for t in tokens:
        if t.dep_ == "nsubj" and t.tag_ in ("NNS", "NNPS"):
            verb = t.head
            if (
                verb.lemma_ == "be"
                and verb.tag_ == "VBD"
                and not time_markers
            ):
                issues.append({
                    "type": "tense_preference",
                    "text_span": sentence[t.idx:verb.idx + len(verb)],
                    "description": "General facts are usually expressed in the present tense."
                })

    # ----------------------------
    # 3. Infinitive clause subject issue
    # ----------------------------
    # "to + verb ... need / require"
    for i, t in enumerate(tokens):
        if t.text.lower() == "to" and i + 1 < len(tokens):
            if tokens[i + 1].pos_ == "VERB":
                later_verbs = [
                    tok for tok in tokens[i + 2:]
                    if tok.lemma_ in ("need", "require")
                ]
                if later_verbs:
                    span_start = t.idx
                    span_end = later_verbs[0].idx + len(later_verbs[0])
                    issues.append({
                        "type": "infinitive_subject_missing",
                        "text_span": sentence[span_start:span_end],
                        "description": "An infinitive clause usually requires a clear subject when followed by a finite verb."
                    })

    return {"issues": issues}
