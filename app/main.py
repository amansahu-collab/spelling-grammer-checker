from fastapi import FastAPI
from pydantic import BaseModel

from app.pipeline.normalize import normalize_text
from app.pipeline.segment import segment_sentences
from app.pipeline.grammar_rules import analyze_grammar_rules
from app.pipeline.grammar_spacy import refine_with_spacy
from app.pipeline.grammar_llm import explain_grammar_errors
from app.pipeline.grammar_score import score_grammar
from app.pipeline.spelling import evaluate_spelling
from app.pipeline.usage_clarity import analyze_usage_clarity
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="PTE Grammar & Spelling Evaluator")


class EvaluateRequest(BaseModel):
    summary: str


@app.post("/evaluate")
def evaluate(payload: EvaluateRequest):
    # STEP 1: normalize
    normalized = normalize_text(payload.summary)

    # STEP 2: segment
    sentences = segment_sentences(normalized)

    # STEP 3 + 4: grammar detection (sentence-level)
    sentence_results = []
    sentence_error_packets = []  # <-- NEW: keep sentence + its errors
    usage_issues = []

    for s in sentences:
        text = s["text"]

        errors = analyze_grammar_rules(text)
        errors = refine_with_spacy(text, errors)

        sentence_results.append(errors)

        # Preserve sentence-level error context for LLM
        sentence_error_packets.append({
            "text": text,
            "errors": errors
        })

        # USAGE / CLARITY (parallel, non-grammar)
        usage = analyze_usage_clarity(text)
        if usage.get("issues"):
            usage_issues.extend(usage["issues"])

    # STEP 6: grammar score (UNCHANGED)
    grammar_score = score_grammar(
        sentence_results=sentence_results,
        sentence_count=len(sentences),
    )

    # --------------------------------------------------
    # BUILD LLM EXPLANATION INPUT (SENTENCE-AWARE)
    # --------------------------------------------------
    explanation_items = []

    for packet in sentence_error_packets:
        sent_text = packet["text"]
        errs = packet["errors"]

        # ---- Span-based errors (precise) ----
        for key, value in errs.items():
            if key.endswith("_spans") and isinstance(value, list):
                err_type = key.replace("_spans", "")
                for span in value:
                    explanation_items.append({
                        "type": err_type,
                        "text_span": span
                    })

        # ---- Structural errors (sentence-level) ----
        STRUCTURAL_ERRORS = [
            "missing_verb",
            "missing_subject",
            "fragment",
            "run_on",
            "tense_error",
            "clause_overload",
        ]

        for err_type in STRUCTURAL_ERRORS:
            if errs.get(err_type, 0) > 0:
                explanation_items.append({
                    "type": err_type,
                    "text_span": sent_text
                })

    # STEP 5: grammar explanation (LLM explains ONLY provided items)
    grammar_explanation = (
        explain_grammar_errors(
            summary=normalized,
            detected_errors={"_items": explanation_items},
        )
        if explanation_items
        else {"errors": []}
    )

    # Spelling
    spelling = evaluate_spelling(normalized)

    return {
        "grammar": {
            "score": grammar_score,
            "details": sentence_results,
            "explanation": grammar_explanation,
        },
        "usage_clarity": {
            "issues": usage_issues
        },
        "spelling": spelling,
    }
