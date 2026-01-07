import streamlit as st
import requests
import json

# ----------------------------
# Config
# ----------------------------
API_URL = "http://localhost:8000/evaluate"  # change if needed

st.set_page_config(
    page_title="Grammar & Usage Analyzer",
    layout="wide"
)

st.title("📝 Grammar, Usage & Spelling Analyzer")

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
        resp = requests.post(API_URL, json={"summary": text})
        result = resp.json()

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
    # Debug (optional)
    # ----------------------------
    with st.expander("🔍 Raw Output (Debug)"):
        st.code(json.dumps(result, indent=2), language="json")
