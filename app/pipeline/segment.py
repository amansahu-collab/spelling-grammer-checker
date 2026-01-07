# app/pipeline/segment.py

import spacy

_nlp = spacy.load("en_core_web_sm")


def segment_sentences(text: str) -> list[dict]:
    """
    STEP 2: Sentence segmentation.

    Rules:
    - Use spaCy sentence boundaries when punctuation exists.
    - If multiple clauses without punctuation (run-on), treat as ONE sentence attempt.
    - Mixed cases allowed: some clean sentences, some run-ons.
    """

    if not text:
        return []

    doc = _nlp(text)

    # spaCy-proposed sentences
    spacy_sents = [sent.text.strip() for sent in doc.sents if sent.text.strip()]

    # If spaCy finds only one sentence, return it as-is
    if len(spacy_sents) <= 1:
        return [{
            "text": text.strip(),
            "type": "normal"
        }]

    # Detect run-on: many verbs, few punctuation marks
    verb_count = sum(1 for t in doc if t.pos_ == "VERB")
    punct_count = sum(1 for t in doc if t.text in {".", "!", "?"})

    if punct_count == 0 and verb_count >= 2:
        # Force single run-on sentence
        return [{
            "text": text.strip(),
            "type": "run-on"
        }]

    # Mixed or clean multiple sentences
    results = []
    for sent in spacy_sents:
        results.append({
            "text": sent,
            "type": "normal"
        })

    return results
