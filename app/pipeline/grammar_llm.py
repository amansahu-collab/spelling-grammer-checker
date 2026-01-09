from llm.router import LLMRouter
import json

_llm = LLMRouter()

# Allowed error types in the system
ALLOWED_ERROR_TYPES = {
    "agreement_error",
    "article_error",
    "tense_error",
    "preposition_error",
    "capitalization_error",
    "missing_verb",
    "missing_subject",
    "fragment",
    "run_on",
    "clause_overload",
    "conjunction_missing",
    "copula_missing",
    "connector_collision",
    "whitespace_error",
}

SYSTEM_PROMPT = """
You are a grammar error explainer.

IMPORTANT RULES:
- You MUST use the provided error `type` exactly as given.
- You MUST NOT invent new error types.
- You MUST NOT change the error type.
- You MUST NOT correct or rewrite the text.
- You MUST ONLY explain why the text span is incorrect.

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
    LLM EXPLAINS ONLY — never classifies or renames errors.
    """

    explanation_items = detected_errors.get("_items", [])
    if not explanation_items:
        return {"errors": []}

    user_prompt = f"""
Student summary:
{summary}

Explain the following grammar errors.
You MUST keep the error type unchanged.

Errors to explain:
{json.dumps(explanation_items, indent=2)}
""".strip()

    try:
        raw = _llm.chat(SYSTEM_PROMPT, user_prompt).strip()
        if not raw.startswith("{"):
            raw = raw[raw.find("{"):]

        data = json.loads(raw)

        # 🔒 HARD SAFETY: enforce allowed error types
        cleaned = []
        for err in data.get("errors", []):
            if err.get("type") in ALLOWED_ERROR_TYPES:
                cleaned.append(err)
            else:
                # fallback: reuse original type
                for src in explanation_items:
                    if src["text_span"] == err.get("text_span"):
                        err["type"] = src["type"]
                        cleaned.append(err)
                        break

        return {"errors": cleaned}

    except Exception:
        return {"errors": []}
