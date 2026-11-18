import streamlit as st
from components.ui_theme import inject_custom_theme, render_html
from components.sidebar import render_sidebar
from utils.api_client import api

st.set_page_config(page_title="Interview Prep — CareerPilot", page_icon="🧭", layout="wide")
inject_custom_theme()
render_sidebar()

candidate = st.session_state.get("candidate")
candidate_id = st.session_state.get("candidate_id")

if not candidate:
    st.warning("Please select or initialize an active candidate in the sidebar.")
    st.stop()

st.title("Interview Preparation Kit")
st.markdown("Role-specific technical questions, project defense talking points, and structured STAR behavioral frameworks.")

# Job Selector
jobs_res = api.get_jobs(page_size=100)
jobs_list = jobs_res.get("items", [])

if not jobs_list:
    st.warning("No jobs in the catalogue.")
    st.stop()

job_options = {j["id"]: f"{j['title']} · {j['company']} ({j['location']})" for j in jobs_list}
job_ids = list(job_options.keys())

default_idx = 0
if "target_interview_job_id" in st.session_state and st.session_state["target_interview_job_id"] in job_ids:
    default_idx = job_ids.index(st.session_state["target_interview_job_id"])

with st.container(border=True):
    c1, c2 = st.columns([3, 1])
    with c1:
        selected_job_id = st.selectbox(
            "Target Job Opportunity",
            options=job_ids,
            index=default_idx,
            format_func=lambda x: job_options.get(x, x)
        )
    with c2:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        gen_clicked = st.button("Generate Prep Kit", type="primary", use_container_width=True)

if gen_clicked:
    with st.spinner("Generating role-tailored technical and behavioral preparation kit..."):
        prep_data = api.generate_interview(candidate_id, selected_job_id)
        if prep_data:
            st.session_state["cached_interview_prep"] = prep_data
            st.session_state["cached_prep_job_id"] = selected_job_id
            st.toast("Interview kit generated successfully!")
        else:
            st.error("Failed to generate interview prep kit. Check backend service.")

# Render Prep Kit
cached = st.session_state.get("cached_interview_prep")
if cached:
    job = api.get_job(st.session_state.get("cached_prep_job_id", selected_job_id))
    company = job.get('company', 'Company') if job else "Company"
    init = "".join([w[0] for w in company.split()[:2]]).upper()

    with st.container(border=True):
        render_html(f"""
        <div style="display: flex; align-items: center;">
            <div class="cp-avatar">{init}</div>
            <div>
                <div style="font-weight: 700; font-size: 1.15rem; color: #0F172A;">{job.get('title') if job else 'Position'}</div>
                <div style="font-size: 0.85rem; color: #64748B;">
                    {company} · {job.get('role_category', '')} · {job.get('experience_level', '')} · {job.get('work_mode', '')}
                </div>
            </div>
        </div>
        """)

    tab_tech, tab_behav, tab_proj, tab_check = st.tabs([
        "Technical Questions",
        "STAR Behavioral Guide",
        "Project Deep Dives",
        "Pre-Interview Checklist"
    ])

    with tab_tech:
        tech_qs = cached.get("technical_questions", [])
        if tech_qs:
            for idx, q in enumerate(tech_qs, 1):
                with st.container(border=True):
                    render_html(f"""
                    <div style="font-weight: 700; font-size: 1.05rem; color: #0F172A; margin-bottom: 0.35rem;">
                        {idx}. {q.get('question')}
                    </div>
                    <div style="font-size: 0.8rem; font-weight: 600; color: #4F46E5; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 0.5rem;">
                        Concept Tested: {q.get('concept_tested')}
                    </div>
                    """)
                    with st.expander("View Answer Outline & Key Points"):
                        st.write(q.get('sample_outline'))
        else:
            st.info("No technical questions generated.")

    with tab_behav:
        behav_qs = cached.get("behavioral_questions", [])
        if behav_qs:
            for idx, b in enumerate(behav_qs, 1):
                star = b.get("star_framework", {})
                with st.container(border=True):
                    render_html(f"""
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
                        <div style="font-weight: 700; font-size: 1.05rem; color: #0F172A;">
                            {idx}. {b.get('question')}
                        </div>
                        <span class="cp-badge cp-badge-brand">{b.get('competency')}</span>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 0.85rem; font-size: 0.85rem; margin-top: 0.5rem;">
                        <div><strong style="color: #4F46E5;">Situation:</strong> {star.get('situation', '')}</div>
                        <div><strong style="color: #4F46E5;">Task:</strong> {star.get('task', '')}</div>
                        <div><strong style="color: #059669;">Action:</strong> {star.get('action', '')}</div>
                        <div><strong style="color: #059669;">Result:</strong> {star.get('result', '')}</div>
                    </div>
                    """)
        else:
            st.info("No behavioral questions generated.")

    with tab_proj:
        proj_qs = cached.get("project_questions", [])
        if proj_qs:
            for idx, p in enumerate(proj_qs, 1):
                with st.container(border=True):
                    render_html(f"""
                    <div style="font-weight: 700; font-size: 1.05rem; color: #0F172A; margin-bottom: 0.35rem;">
                        {idx}. {p.get('question')}
                    </div>
                    <p style="font-size: 0.85rem; color: #64748B; margin-bottom: 0.5rem;">
                        <strong>Context:</strong> {p.get('context')}
                    </p>
                    <div style="background: #EEF2FF; border-left: 3px solid #4F46E5; padding: 0.6rem 0.85rem; font-size: 0.85rem; color: #312E81;">
                        <strong>Talking Points:</strong> {p.get('suggested_focus')}
                    </div>
                    """)
        else:
            st.info("No project defense questions generated.")

    with tab_check:
        checklist = cached.get("checklist_items", [])
        if checklist:
            for idx, item in enumerate(checklist, 1):
                c_col1, c_col2 = st.columns([4, 1])
                with c_col1:
                    render_html(f"""
                    <div style="margin-bottom: 0.5rem;">
                        <div style="font-weight: 600; font-size: 0.92rem; color: #0F172A;">{item.get('title')}</div>
                        <div style="font-size: 0.825rem; color: #64748B;">{item.get('description')}</div>
                    </div>
                    """)
                with c_col2:
                    if st.button("Add to Tasks", key=f"add_chk_{idx}", use_container_width=True):
                        api.create_task(candidate_id, {
                            "job_id": selected_job_id,
                            "title": item.get('title'),
                            "description": item.get('description'),
                            "task_type": "preparation",
                            "priority": "high"
                        })
                        st.toast(f"Added task: {item.get('title')}")
                st.divider()
        else:
            st.info("No checklist items generated.")
