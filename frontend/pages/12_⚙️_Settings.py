import streamlit as st
import sys
import os
from components.ui_theme import inject_custom_theme, render_html
from components.sidebar import render_sidebar
from utils.api_client import api

st.set_page_config(page_title="Settings — CareerPilot", page_icon="🧭", layout="wide")
inject_custom_theme()
render_sidebar()

st.title("System Diagnostics & Settings")
st.markdown("Inspect backend health, local LLM connectivity, and manage database operations.")

# LLM Configuration
st.subheader("Local LLM Configuration")
health = api.get_health()
llm_health = health.get("llm_service", {})
db_connected = health.get("database_connected", False)

with st.container(border=True):
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        st.markdown(f"**Ollama Endpoint:** `http://localhost:11434`")
        st.markdown(f"**Target Model:** `{llm_health.get('model', 'llama3.2:3b')}`")
        is_fb = llm_health.get("is_fallback", True)
        if not is_fb and llm_health.get("status") == "connected":
            st.success("Ollama Service Connected & Healthy")
        else:
            st.warning("Ollama Offline — Deterministic Rule-Based Engine Active")
            st.caption("All features execute locally with deterministic algorithms.")

    with col_l2:
        st.markdown("#### Test Connection")
        if st.button("Check Ollama Status", use_container_width=True):
            h_refresh = api.get_health()
            if not h_refresh.get("llm_service", {}).get("is_fallback", True):
                st.success("Ollama is reachable!")
            else:
                st.warning("Ollama server not detected on port 11434.")

# Database
st.subheader("Database & Vector Index")
with st.container(border=True):
    c_db1, c_db2 = st.columns(2)
    with c_db1:
        st.markdown(f"**Storage Engine:** `SQLite 3 (ACID Local Storage)`")
        st.markdown(f"**Status:** {'Connected' if db_connected else 'Disconnected'}")
        
        jobs_res = api.get_jobs(page_size=1)
        tot_jobs = jobs_res.get("total", 0)
        st.markdown(f"**Indexed Job Postings:** `{tot_jobs:,}`")
        
        cands = api.list_candidates()
        st.markdown(f"**Registered Candidates:** `{len(cands)}`")

    with c_db2:
        st.markdown("#### Catalogue Seeding")
        if st.button("Re-import Sample Jobs (250 Records)", use_container_width=True):
            with st.spinner("Importing sample dataset from CSV..."):
                res = api.import_sample_jobs()
                st.toast(res.get("message", "Import process completed!"))
                st.rerun()

# Runtime
st.subheader("Runtime Environment")
with st.container(border=True):
    e1, e2 = st.columns(2)
    with e1:
        st.markdown(f"**Python Version:** `{sys.version.split()[0]}`")
        st.markdown(f"**Executable:** `{sys.executable}`")
        st.markdown(f"**Working Directory:** `{os.getcwd()}`")
    with e2:
        st.markdown(f"**Application Version:** `1.0.0`")
        st.markdown(f"**FastAPI Backend URL:** `{api.base_url}`")
        st.markdown(f"**Retrieval Engine:** `In-Memory TF-IDF Vectorizer + Cosine Similarity`")
