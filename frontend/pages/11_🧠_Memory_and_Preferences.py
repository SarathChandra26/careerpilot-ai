import streamlit as st
from components.ui_theme import inject_custom_theme, render_html
from components.sidebar import render_sidebar
from utils.api_client import api

st.set_page_config(page_title="Candidate Memory — CareerPilot", page_icon="🧭", layout="wide")
inject_custom_theme()
render_sidebar()

candidate = st.session_state.get("candidate")
candidate_id = st.session_state.get("candidate_id")

if not candidate:
    st.warning("Please select or initialize an active candidate in the sidebar.")
    st.stop()

st.title("Candidate Long-Term Memory")
st.markdown("Persistent contextual preferences, constraints, and career targets retained by the AI Agent across sessions.")

col_memories, col_add = st.columns([3, 2])

memories = api.get_memories(candidate_id)

with col_memories:
    st.subheader("Retained Context Items")
    
    if memories:
        grouped = {}
        for m in memories:
            cat = m.get("category", "preference")
            grouped.setdefault(cat, []).append(m)

        for cat, items in grouped.items():
            render_html(f"<div style='font-size: 0.85rem; font-weight: 700; text-transform: uppercase; color: #64748B; margin: 0.75rem 0 0.35rem 0;'>{cat.title()} Context</div>")
            for idx, item in enumerate(items):
                m_id = item.get("id")
                with st.container(border=True):
                    c_info, c_act = st.columns([4, 1])
                    with c_info:
                        st.markdown(f"**{item.get('memory_key')}**")
                        st.markdown(f"<span style='color: #475569; font-size: 0.875rem;'>{item.get('memory_value')}</span>", unsafe_allow_html=True)
                        st.caption(f"Confidence: {item.get('confidence', 1.0) * 100:.0f}% · Source: {item.get('source', 'user')}")
                    with c_act:
                        if st.button("Delete", key=f"del_mem_{m_id}_{idx}", type="secondary", use_container_width=True):
                            api.delete_memory(m_id)
                            st.toast("Memory item removed.")
                            st.rerun()
    else:
        st.info("No long-term memories stored yet. Conversing with the assistant automatically extracts context.")

with col_add:
    st.subheader("Add Explicit Context")
    st.caption("Inject specific guidance that the agent must prioritize during job matching.")
    
    with st.container(border=True):
        with st.form("new_memory_form"):
            mem_key = st.text_input("Memory Key", placeholder="e.g. target_work_mode, salary_floor")
            mem_val = st.text_area("Memory Value", placeholder="e.g. Prefers fully remote or hybrid roles in California")
            mem_cat = st.selectbox("Category", ["preference", "goal", "constraint", "skill_note", "general"], index=0)
            mem_conf = st.slider("Confidence", min_value=0.5, max_value=1.0, value=1.0, step=0.05)
            
            sub_mem = st.form_submit_button("Save to Memory", type="primary", use_container_width=True)
            if sub_mem and mem_key and mem_val:
                api.create_memory(candidate_id, mem_key.strip(), mem_val.strip(), category=mem_cat, confidence=mem_conf)
                st.toast("Context stored!")
                st.rerun()

st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
with st.container(border=True):
    render_html("""
    <div style="border-left: 4px solid #4F46E5; padding-left: 1rem;">
        <div style="font-weight: 700; font-size: 0.95rem; color: #0F172A; margin-bottom: 0.25rem;">Privacy Guarantee</div>
        <p style="font-size: 0.85rem; color: #475569; margin: 0; line-height: 1.45;">
            All memories are stored locally in your SQLite database. No data is sent to external servers or shared across candidates.
        </p>
    </div>
    """)
