import streamlit as st
from components.ui_theme import inject_custom_theme, render_html
from components.sidebar import render_sidebar
from utils.api_client import api

st.set_page_config(page_title="Resume Analysis — CareerPilot", page_icon="🧭", layout="wide")
inject_custom_theme()
render_sidebar()

candidate = st.session_state.get("candidate")
candidate_id = st.session_state.get("candidate_id")

if not candidate:
    st.warning("Please select or initialize an active candidate profile first.")
    st.stop()

st.title("Resume Parsing & Ingestion")
st.markdown("Upload your resume in PDF, DOCX, or TXT format. CareerPilot extracts competencies, education, and credentials to synchronize with your profile.")

col_upload, col_history = st.columns([3, 2])

with col_upload:
    with st.container(border=True):
        st.subheader("Upload Document")
        uploaded_file = st.file_uploader("Select Resume File", type=["pdf", "docx", "doc", "txt"], label_visibility="collapsed")
        
        if uploaded_file is not None:
            render_html(f"""
            <div style="background: #F1F5F9; border-radius: 8px; padding: 0.6rem 0.85rem; font-size: 0.85rem; margin: 0.75rem 0;">
                <strong>Selected:</strong> {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)
            </div>
            """)
            if st.button("Parse and Update Profile", type="primary", use_container_width=True):
                with st.spinner("Extracting text and identifying technical competencies..."):
                    bytes_data = uploaded_file.getvalue()
                    result = api.upload_resume(candidate_id, uploaded_file.name, bytes_data)
                    
                    if result:
                        st.toast("Resume parsed and profile updated successfully!")
                        cand_updated = api.get_candidate(candidate_id)
                        if cand_updated:
                            st.session_state["candidate"] = cand_updated
                        st.session_state["last_parsed_resume"] = result
                        st.rerun()
                    else:
                        st.error("Failed to parse resume.")

with col_history:
    with st.container(border=True):
        st.subheader("Stored Documents")
        resumes = api.list_resumes(candidate_id)
        if resumes:
            for idx, r in enumerate(resumes):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"**{r.get('filename')}**")
                    st.caption(f"Format: `{r.get('file_type', '').upper()}` · {r.get('uploaded_at', '')[:10]}")
                with c2:
                    if st.button("Delete", key=f"del_res_{r.get('id')}_{idx}", type="secondary"):
                        api.delete_resume(r.get('id'))
                        st.toast("Resume deleted.")
                        st.rerun()
                st.divider()
        else:
            st.info("No resumes uploaded yet.")

# Parsed Results
last_parsed = st.session_state.get("last_parsed_resume")
if last_parsed and "parsed_data" in last_parsed:
    pd = last_parsed["parsed_data"]
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    st.subheader(f"Extracted Credentials: {last_parsed.get('filename')}")
    
    with st.container(border=True):
        e1, e2, e3 = st.columns(3)
        with e1:
            st.markdown(f"**Full Name:** {pd.get('full_name') or 'Not specified'}")
            st.markdown(f"**Email:** {pd.get('email') or 'Not specified'}")
            st.markdown(f"**Phone:** {pd.get('phone') or 'Not specified'}")
        with e2:
            st.markdown(f"**Education:** {pd.get('education') or 'Not specified'}")
            st.markdown(f"**Degree:** {pd.get('degree') or 'Not specified'}")
            st.markdown(f"**Experience:** {pd.get('experience_years', 0)} years")
        with e3:
            st.markdown(f"**Interests:** {', '.join(pd.get('career_interests', [])) or 'None detected'}")

        render_html("<div style='font-size: 0.85rem; font-weight: 700; text-transform: uppercase; color: #64748B; margin: 1rem 0 0.5rem 0;'>Detected Technical Skills</div>")
        skills = pd.get("skills", [])
        if skills:
            chips = " ".join([f"<span class='cp-badge cp-badge-brand'>{s}</span>" for s in skills])
            render_html(chips)

        if pd.get("raw_text_preview"):
            with st.expander("View Raw Extracted Text"):
                st.text(pd.get("raw_text_preview"))
