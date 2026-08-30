from __future__ import annotations

import streamlit as st

from decisionos.agent.orchestrator import answer_question
from decisionos.db.connection import list_repos

st.set_page_config(page_title="Codebase Intelligence", layout="wide")
st.title("Codebase Intelligence")
st.caption(
    "Ask a question about a parsed repository — answers are grounded in retrieved code "
    "and import relationships, not the model's memory."
)

repos = list_repos()
if not repos:
    st.warning(
        "No repos have been parsed yet. Run `scripts/build_codemap.py` and "
        "`scripts/build_embeddings.py` on a repo first."
    )
    st.stop()

repo_id = st.selectbox("Repo", repos)
question = st.text_input("Ask a question about the codebase", placeholder="Where is the model trained?")
ask = st.button("Ask")

if ask and question:
    with st.spinner("Searching code and asking the model..."):
        result = answer_question(question, repo_id)

    st.subheader("Answer")
    st.write(result["answer"])

    if result["graph_context"]:
        st.subheader("Dependency context")
        st.code(result["graph_context"], language="text")

    if result["call_context"]:
        st.subheader("Call graph context")
        st.code(result["call_context"], language="text")

    st.subheader("Evidence")
    for chunk in result["evidence"]:
        with st.expander(f"{chunk['node_id']}  (similarity {chunk['score']:.2f})"):
            st.code(chunk["content"], language="python")
