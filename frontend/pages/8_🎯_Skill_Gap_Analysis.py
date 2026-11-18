import streamlit as st
import plotly.express as px
import pandas as pd
from components.ui_theme import inject_custom_theme, render_html
from components.sidebar import render_sidebar
from utils.api_client import api

st.set_page_config(page_title="Skill Gap Audit — CareerPilot", page_icon="🧭", layout="wide")
inject_custom_theme()
render_sidebar()

candidate = st.session_state.get("candidate")
candidate_id = st.session_state.get("candidate_id")

if not candidate:
    st.warning("Please select or initialize an active candidate in the sidebar.")
    st.stop()

st.title("Skill Gap Audit & Learning Roadmap")
st.markdown("Diagnose technical competency gaps for any vacancy and follow a structured roadmap to reach 100% eligibility.")

# Job Selector
jobs_res = api.get_jobs(page_size=100)
jobs_list = jobs_res.get("items", [])

if not jobs_list:
    st.warning("No jobs in the catalogue.")
    st.stop()

job_options = {j["id"]: f"{j['title']} · {j['company']} ({j['location']})" for j in jobs_list}
job_ids = list(job_options.keys())

default_idx = 0
if "target_gap_job_id" in st.session_state and st.session_state["target_gap_job_id"] in job_ids:
    default_idx = job_ids.index(st.session_state["target_gap_job_id"])

with st.container(border=True):
    selected_job_id = st.selectbox(
        "Target Job Opportunity",
        options=job_ids,
        index=default_idx,
        format_func=lambda x: job_options.get(x, x)
    )

if selected_job_id:
    job = api.get_job(selected_job_id)
    gaps = api.get_skill_gaps(candidate_id, selected_job_id)

    if job and gaps:
        readiness = gaps.get("readiness_score", 0.0)
        company = job.get("company", "Company")
        init = "".join([w[0] for w in company.split()[:2]]).upper()
        score_color = '#059669' if readiness >= 75 else '#4F46E5' if readiness >= 50 else '#D97706'

        with st.container(border=True):
            render_html(f"""
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center;">
                    <div class="cp-avatar">{init}</div>
                    <div>
                        <div style="font-weight: 700; font-size: 1.2rem; color: #0F172A;">{job.get('title')}</div>
                        <div style="font-size: 0.875rem; color: #64748B;">
                            {company} · {job.get('role_category')} · {job.get('work_mode')} · {job.get('experience_level')}
                        </div>
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 1.6rem; font-weight: 800; color: {score_color};">
                        {readiness:.1f}%
                    </div>
                    <div style="font-size: 0.72rem; text-transform: uppercase; font-weight: 600; color: #64748B;">Role Readiness</div>
                </div>
            </div>
            """)

        col_chart, col_skills = st.columns([1, 1])

        matched_skills = gaps.get("matched_skills", [])
        missing_req = gaps.get("missing_required_skills", [])
        missing_pref = gaps.get("missing_preferred_skills", [])

        with col_chart:
            st.subheader("Competency Distribution")
            chart_data = {
                "Category": ["Matched Competencies", "Missing Required", "Missing Preferred"],
                "Count": [len(matched_skills), len(missing_req), len(missing_pref)]
            }
            df_gaps = pd.DataFrame(chart_data)
            fig_gaps = px.pie(
                df_gaps,
                names="Category",
                values="Count",
                hole=0.6,
                color="Category",
                color_discrete_map={
                    "Matched Competencies": "#10B981",
                    "Missing Required": "#EF4444",
                    "Missing Preferred": "#F59E0B"
                }
            )
            fig_gaps.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                height=250,
                font={"family": "Plus Jakarta Sans"},
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_gaps, use_container_width=True)

        with col_skills:
            st.subheader("Competency Audit")
            with st.container(border=True):
                render_html(f"""
                <div style="margin-bottom: 0.75rem;">
                    <div style="font-size: 0.78rem; text-transform: uppercase; font-weight: 700; color: #059669; margin-bottom: 4px;">Verified Matches ({len(matched_skills)})</div>
                    <div style="font-size: 0.85rem; color: #0F172A;">{', '.join(matched_skills) if matched_skills else 'No overlapping skills'}</div>
                </div>
                <div style="margin-bottom: 0.75rem;">
                    <div style="font-size: 0.78rem; text-transform: uppercase; font-weight: 700; color: #DC2626; margin-bottom: 4px;">Missing Required ({len(missing_req)})</div>
                    <div style="font-size: 0.85rem; color: #0F172A;">{', '.join(missing_req) if missing_req else 'All required skills covered'}</div>
                </div>
                <div>
                    <div style="font-size: 0.78rem; text-transform: uppercase; font-weight: 700; color: #D97706; margin-bottom: 4px;">Missing Preferred ({len(missing_pref)})</div>
                    <div style="font-size: 0.85rem; color: #64748B;">{', '.join(missing_pref) if missing_pref else 'No missing preferred skills'}</div>
                </div>
                """)

        st.subheader("Personalized Learning Roadmap")
        roadmap = gaps.get("learning_roadmap", [])

        if roadmap:
            for idx, item in enumerate(roadmap, 1):
                prio = item.get("priority", "High")
                prio_class = "cp-badge-danger" if prio.lower() == "high" else "cp-badge-warning"
                
                with st.container(border=True):
                    render_html(f"""
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
                        <div>
                            <span style="font-weight: 700; font-size: 1.1rem; color: #0F172A;">{idx}. {item.get('skill_name')}</span>
                            <span class="cp-badge {prio_class}" style="margin-left: 0.5rem;">{prio} Priority</span>
                            <span class="cp-badge cp-badge-neutral">{item.get('estimated_weeks', 2)} Weeks</span>
                        </div>
                    </div>
                    <p style="font-size: 0.875rem; color: #475569; line-height: 1.5; margin-bottom: 0.5rem;">
                        <strong>Why It Matters:</strong> {item.get('rationale')}
                    </p>
                    <p style="font-size: 0.875rem; color: #475569; line-height: 1.5; margin-bottom: 0.5rem;">
                        <strong>Recommended Study:</strong> {item.get('resources')}
                    </p>
                    <p style="font-size: 0.875rem; color: #0F172A; line-height: 1.5; margin-bottom: 0.75rem;">
                        <strong>Proof Project Idea:</strong> {item.get('project_idea')}
                    </p>
                    """)
                    if st.button(f"Mark Learned & Add '{item.get('skill_name')}' to Profile", key=f"learn_{item.get('skill_name')}"):
                        api.add_skill(candidate_id, item.get('skill_name'), category="Self-Learned", proficiency="Intermediate")
                        cand_ref = api.get_candidate(candidate_id)
                        st.session_state["candidate"] = cand_ref
                        st.toast(f"Added {item.get('skill_name')} to your profile skills!")
                        st.rerun()
        else:
            st.success("Your stack covers 100% of the competencies for this role!")
