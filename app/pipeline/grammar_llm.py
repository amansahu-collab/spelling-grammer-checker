from llm.router import LLMRouter
import json

_llm = LLMRouter()

SYSTEM_PROMPT = """
You are a grammar error explainer.

You will be given:
- A student summary
- Grammar errors with EXACT text spans already identified by the system

Your task:
- Explain WHY each given span is grammatically incorrect.
- Do NOT change the span.
- Do NOT invent new errors.
- Do NOT merge errors.
- Do NOT rewrite or correct anything.
- Do NOT give suggestions.

If no errors are provided, return an empty list.

Output ONLY valid JSON in this exact format:

{
  "errors": [
    {
      "type": "error_type",
      "text_span": "exact text span provided",
      "description": "one short sentence explaining why this is grammatically incorrect"
    }
  ]
}
""".strip()


def explain_grammar_errors(summary: str, detected_errors: dict) -> dict:
    """
    STEP 5: LLM-based grammar explanation.
    Locations come ONLY from rule-based logic.
    LLM explains, never locates.
    """

    if not summary:
        return {"errors": []}

    explanation_items = []

    # ---- Existing error types ----
    for span in detected_errors.get("conjunction_missing_spans", []):
        explanation_items.append({
            "type": "conjunction_missing",
            "text_span": span
        })

    for span in detected_errors.get("article_error_spans", []):
        explanation_items.append({
            "type": "article_error",
            "text_span": span
        })

    for span in detected_errors.get("preposition_error_spans", []):
        explanation_items.append({
            "type": "preposition_error",
            "text_span": span
        })

    for span in detected_errors.get("capitalization_error_spans", []):
        explanation_items.append({
            "type": "capitalization_error",
            "text_span": span
        })

    for span in detected_errors.get("agreement_error_spans", []):
        explanation_items.append({
            "type": "agreement_error",
            "text_span": span
        })

    # ---- NEW diagnostic error types ----

    for span in detected_errors.get("agreement_error_v2_spans", []):
        explanation_items.append({
            "type": "agreement_error",
            "text_span": span
        })

    for span in detected_errors.get("copula_missing_spans", []):
        explanation_items.append({
            "type": "missing_verb",
            "text_span": span
        })

    for span in detected_errors.get("connector_collision_spans", []):
        explanation_items.append({
            "type": "connector_collision",
            "text_span": span
        })

    for span in detected_errors.get("whitespace_error_spans", []):
        explanation_items.append({
            "type": "whitespace_error",
            "text_span": span
        })

    # ---- Clause overload (global) ----
    if detected_errors.get("clause_overload", 0) > 0:
        explanation_items.append({
            "type": "clause_overload",
            "text_span": summary
        })

    if not explanation_items:
        return {"errors": []}

    user_prompt = f"""
Student summary:
{summary}

Explain the following grammar errors.
Use the PROVIDED text spans exactly as given.

Errors to explain:
{json.dumps(explanation_items, indent=2)}
""".strip()

    try:
        raw = _llm.chat(SYSTEM_PROMPT, user_prompt)
        raw = raw.strip()

        if not raw.startswith("{"):
            raw = raw[raw.find("{"):]

        return json.loads(raw)

    except Exception:
        # Explanation failure must NEVER break evaluation
        return {"errors": []}
