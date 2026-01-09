import streamlit as st
import json

# ----------------------------
# Pipeline imports
# ----------------------------
from pipeline.normalize import normalize_text
from pipeline.segment import segment_sentences
from pipeline.grammar_rules import analyze_grammar_rules
from pipeline.grammar_spacy import refine_with_spacy
from pipeline.grammar_llm import explain_grammar_errors
from pipeline.grammar_score import score_grammar
from pipeline.spelling import evaluate_spelling
from pipeline.usage_clarity import analyze_usage_clarity


# ----------------------------
# Streamlit config
# ----------------------------
st.set_page_config(
    page_title="Grammar & Usage Analyzer",
    layout="wide"
)

st.title("📝 Grammar & Spelling Checker")

# ----------------------------
# Input
# ----------------------------
text = st.text_area(
    "Enter text to evaluate",
    height=180,
    placeholder="Paste the student's response here..."
)

if st.button("Analyze"):
    if not text.strip():
        st.warning("Please enter some text.")
        st.stop()

    with st.spinner("Analyzing..."):
        # STEP 1: normalize
        normalized = normalize_text(text)

        # STEP 2: segment
        sentences = segment_sentences(normalized)

        sentence_results = []
        sentence_error_packets = []
        usage_issues = []

        for s in sentences:
            sent_text = s["text"]

            errors = analyze_grammar_rules(sent_text)
            errors = refine_with_spacy(sent_text, errors)

            sentence_results.append(errors)
            sentence_error_packets.append({
                "text": sent_text,
                "errors": errors
            })

            usage = analyze_usage_clarity(sent_text)
            if usage.get("issues"):
                usage_issues.extend(usage["issues"])

        # STEP 3: grammar score
        grammar_score = score_grammar(
            sentence_results=sentence_results,
            sentence_count=len(sentences),
        )

        # --------------------------------------------------
        # BUILD CLEAN LLM EXPLANATION ITEMS (FINAL FIX)
        # --------------------------------------------------
        explanation_items = []
        _seen = set()

        for packet in sentence_error_packets:
            sent_text = packet["text"]
            errs = packet["errors"]

            # ---- Span-based errors ONLY ----
            for key, value in errs.items():
                if key.endswith("_spans") and isinstance(value, list):
                    err_type = key.replace("_spans", "")
                    for span in value:
                        if not span or not isinstance(span, str):
                            continue
                        k = (err_type, span)
                        if k not in _seen:
                            explanation_items.append({
                                "type": err_type,
                                "text_span": span
                            })
                            _seen.add(k)

            # ---- Structural errors (sentence-level ONLY when no span exists) ----
            STRUCTURAL_ERRORS = [
                "missing_verb",
                "missing_subject",
                "fragment",
                "run_on",
                "clause_overload",
            ]

            for err_type in STRUCTURAL_ERRORS:
                if errs.get(err_type, 0) > 0:
                    k = (err_type, sent_text)
                    if k not in _seen:
                        explanation_items.append({
                            "type": err_type,
                            "text_span": sent_text
                        })
                        _seen.add(k)

        grammar_explanation = (
            explain_grammar_errors(
                summary=normalized,
                detected_errors={"_items": explanation_items},
            )
            if explanation_items
            else {"errors": []}
        )

        spelling = evaluate_spelling(normalized)

        result = {
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

    # ----------------------------
    # Layout
    # ----------------------------
    grammar = result.get("grammar", {})
    usage = result.get("usage_clarity", {})
    spelling = result.get("spelling", {})

    col1, col2, col3 = st.columns([1.2, 1.2, 0.8])

    # ============================
    # GRAMMAR
    # ============================
    with col1:
        st.subheader("📘 Grammar")

        st.metric(
            label="Grammar Score",
            value=f"{grammar.get('score', 0)} / 4"
        )

        explanations = grammar.get("explanation", {}).get("errors", [])

        if not explanations:
            st.success("No grammar errors detected.")
        else:
            for err in explanations:
                st.error(f"**{err['type']}**")
                st.markdown(f"**Text:** `{err['text_span']}`")
                st.markdown(f"**Why:** {err['description']}")
                st.divider()

    # ============================
    # USAGE / CLARITY
    # ============================
    with col2:
        st.subheader("💡 Usage & Clarity (No Penalty)")

        issues = usage.get("issues", [])

        if not issues:
            st.success("No usage or clarity issues.")
        else:
            for issue in issues:
                st.warning(f"**{issue['type']}**")
                st.markdown(f"**Text:** `{issue['text_span']}`")
                st.markdown(f"**Note:** {issue['description']}")
                st.divider()

    # ============================
    # SPELLING
    # ============================
    with col3:
        st.subheader("🔤 Spelling")

        st.metric(
            label="Spelling Score",
            value=f"{spelling.get('spelling_score', 0)} / 4"
        )

        misspelled = spelling.get("misspelled_words", [])

        if not misspelled:
            st.success("No spelling mistakes.")
        else:
            st.error(f"{len(misspelled)} misspelled words")
            for w in misspelled:
                st.write(f"• `{w}`")

    # ----------------------------
    # Debug
    # ----------------------------
    with st.expander("🔍 Raw Output (Debug)"):
        st.code(json.dumps(result, indent=2), language="json")
