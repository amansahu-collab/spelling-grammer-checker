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

    # STEP 3 + 4: grammar detection
    sentence_results = []
    usage_issues = []

    for s in sentences:
        text = s["text"]

        errors = analyze_grammar_rules(text)
        errors = refine_with_spacy(text, errors)
        sentence_results.append(errors)

        # USAGE / CLARITY (parallel, non-grammar)
        usage = analyze_usage_clarity(text)
        if usage.get("issues"):
            usage_issues.extend(usage["issues"])

    # STEP 6: grammar score (unchanged)
    grammar_score = score_grammar(
        sentence_results=sentence_results,
        sentence_count=len(sentences),
    )

    # --------------------------------------------------
    # AGGREGATE ERRORS + SPANS (GRAMMAR ONLY)
    # --------------------------------------------------
    aggregated_errors = {}

    for result in sentence_results:
        for key, value in result.items():
            if key.endswith("_spans") and isinstance(value, list):
                aggregated_errors.setdefault(key, []).extend(value)
            elif isinstance(value, int):
                aggregated_errors[key] = aggregated_errors.get(key, 0) + value

    # STEP 5: grammar explanation (LLM explains ONLY grammar)
    grammar_explanation = explain_grammar_errors(
        summary=normalized,
        detected_errors=aggregated_errors,
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
