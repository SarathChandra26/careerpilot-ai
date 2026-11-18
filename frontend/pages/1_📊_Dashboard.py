import streamlit as st
import plotly.express as px
import pandas as pd
from components.ui_theme import inject_custom_theme, render_html, CHART_THEME
from components.sidebar import render_sidebar
from utils.api_client import api

st.set_page_config(page_title="Dashboard — CareerPilot", page_icon="🧭", layout="wide")
inject_custom_theme()
render_sidebar()

candidate = st.session_state.get("candidate")
candidate_id = st.session_state.get("candidate_id")

if not candidate:
    st.warning("Please select or initialize an active candidate in the sidebar.")
    st.stop()

st.title("Career Overview")
st.markdown(f"Live analytics, opportunity matching, and pipeline activity for **{candidate.get('full_name')}**.")

# Profile Completeness Banner
comp_score = candidate.get("completeness_score", 0.0)
badge_class = 'cp-badge-success' if comp_score >= 80 else 'cp-badge-warning'
badge_text = 'Strong Match Readiness' if comp_score >= 80 else 'Action Recommended'

with st.container(border=True):
    render_html(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
        <div>
            <span style="font-weight: 700; font-size: 1.05rem; color: #0F172A;">Profile Optimization</span>
            <span style="font-size: 0.85rem; color: #64748B; margin-left: 0.5rem;">({comp_score:.0f}% Complete)</span>
        </div>
        <span class="cp-badge {badge_class}">
            {badge_text}
        </span>
    </div>
    """)
    st.progress(min(1.0, max(0.0, comp_score / 100.0)))

    missing_sections = []
    if not candidate.get("phone"):
        missing_sections.append("Contact Number")
    if not candidate.get("skills") or len(candidate.get("skills", [])) < 5:
        missing_sections.append("Register 5+ core skills")
    if not candidate.get("career_interests"):
        missing_sections.append("Target career interests")

    if missing_sections:
        st.caption(f"Suggested profile improvements: **{', '.join(missing_sections)}**")
    else:
        st.caption("Your profile is fully configured for multi-factor candidate matching.")

    c_btn1, c_btn2, _ = st.columns([1, 1, 3])
    with c_btn1:
        st.page_link("pages/2_👤_My_Profile.py", label="Edit Profile Details", use_container_width=True)
    with c_btn2:
        st.page_link("pages/3_📄_Resume_Analysis.py", label="Upload New Resume", use_container_width=True)

# Metrics Grid
m1, m2, m3, m4 = st.columns(4)

jobs_res = api.get_jobs(page_size=1)
total_jobs = jobs_res.get("total", 0)
saved_jobs = api.get_saved_jobs(candidate_id)
apps = api.get_applications(candidate_id)
tasks = api.get_tasks(candidate_id, is_completed=False)

with m1:
    render_html(f"""
    <div class="cp-stat-card">
        <div class="cp-stat-label">Total Curated Jobs</div>
        <div class="cp-stat-value">{total_jobs:,}</div>
        <div class="cp-stat-sub">Across 10 categories</div>
    </div>
    """)
with m2:
    render_html(f"""
    <div class="cp-stat-card">
        <div class="cp-stat-label">Saved Opportunities</div>
        <div class="cp-stat-value">{len(saved_jobs)}</div>
        <div style="font-size: 0.8rem; font-weight: 500; color: #64748B; margin-top: 0.25rem;">For later review</div>
    </div>
    """)
with m3:
    render_html(f"""
    <div class="cp-stat-card">
        <div class="cp-stat-label">Active Applications</div>
        <div class="cp-stat-value">{len(apps)}</div>
        <div style="font-size: 0.8rem; font-weight: 500; color: #6366F1; margin-top: 0.25rem;">In pipeline</div>
    </div>
    """)
with m4:
    render_html(f"""
    <div class="cp-stat-card">
        <div class="cp-stat-label">Pending Checklist Tasks</div>
        <div class="cp-stat-value">{len(tasks)}</div>
        <div style="font-size: 0.8rem; font-weight: 500; color: #F59E0B; margin-top: 0.25rem;">Preparation items</div>
    </div>
    """)

st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

# Main Dashboard Columns: Recommendations & Pipeline Breakdown
col_left, col_right = st.columns([3, 2])

recs_data = api.get_recommendations(candidate_id, limit=6)
recs = recs_data.get("recommendations", [])

with col_left:
    st.subheader("High-Affinity Recommendations")
    if recs:
        for idx, r in enumerate(recs[:3]):
            job_obj = r.get("job") or {}
            job_id = job_obj.get("id") or r.get("job_id", f"dash_job_{idx}")
            title = job_obj.get("title") or r.get("title", "Opportunity")
            company = job_obj.get("company") or r.get("company", "Company")
            location = job_obj.get("location") or r.get("location", "Remote")
            work_mode = job_obj.get("work_mode") or r.get("work_mode", "Remote")
            sal_min = job_obj.get("salary_min")
            sal_max = job_obj.get("salary_max")
            sal_text = f"${sal_min:,} - ${sal_max:,}" if sal_min and sal_max else "Competitive"
            matched = r.get("matched_required_skills", []) + r.get("matched_preferred_skills", [])
            initials = "".join([w[0] for w in company.split()[:2]]).upper() or "CO"
            score = r.get("overall_score", 0.0)
            score_color = "#059669" if score >= 75 else "#4F46E5" if score >= 55 else "#D97706"
            badge_bg = "#ECFDF5" if score >= 75 else "#EEF2FF" if score >= 55 else "#FFFBEB"

            with st.container(border=True):
                render_html(f"""
                <div>
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
                        <div style="display: flex; align-items: center;">
                            <div class="cp-avatar">{initials}</div>
                            <div>
                                <div style="font-weight: 700; font-size: 1.05rem; color: #0F172A;">{title}</div>
                                <div style="font-size: 0.85rem; color: #64748B;">{company} · {location}</div>
                            </div>
                        </div>
                        <span style="background: {badge_bg}; color: {score_color}; font-weight: 700; font-size: 0.85rem; padding: 4px 10px; border-radius: 9999px;">
                            {score:.1f}% Match
                        </span>
                    </div>
                    <div style="margin-bottom: 0.5rem;">
                        <span class="cp-badge cp-badge-neutral">{work_mode}</span>
                        <span class="cp-badge cp-badge-neutral">{sal_text}</span>
                    </div>
                    <div style="font-size: 0.825rem; color: #475569; margin-bottom: 0.75rem;">
                        <span style="color: #059669; font-weight: 600;">Matched:</span> {', '.join(matched[:4]) if matched else 'None'}
                    </div>
                </div>
                """)
                b1, b2 = st.columns([1, 1])
                with b1:
                    if st.button("Save Opportunity", key=f"dash_save_{job_id}_{idx}", use_container_width=True):
                        api.save_job(candidate_id, job_id)
                        st.toast("Saved opportunity to profile!")
                with b2:
                    if st.button("Skill Gap Analysis →", key=f"dash_gap_{job_id}_{idx}", use_container_width=True):
                        st.session_state["target_gap_job_id"] = job_id
                        st.switch_page("pages/8_🎯_Skill_Gap_Analysis.py")

        st.page_link("pages/6_⭐_Job_Recommendations.py", label="View all personalized recommendations →")
    else:
        st.info("No recommendations generated yet. Try verifying your skills in My Profile.")

with col_right:
    st.subheader("Application Pipeline")
    if apps:
        status_counts = {}
        for a in apps:
            s = a.get("status", "Interested")
            status_counts[s] = status_counts.get(s, 0) + 1
        df_status = pd.DataFrame(list(status_counts.items()), columns=["Stage", "Count"])
        fig_pipe = px.pie(
            df_status,
            names="Stage",
            values="Count",
            hole=0.6,
            color_discrete_sequence=["#4F46E5", "#10B981", "#F59E0B", "#6366F1", "#EC4899", "#8B5CF6"]
        )
        fig_pipe.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            height=240,
            font={"family": "Plus Jakarta Sans"},
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_pipe, use_container_width=True)
    else:
        with st.container(border=True):
            render_html("""
            <div style="text-align: center; padding: 1.5rem 1rem;">
                <div style="font-weight: 600; color: #475569; margin-bottom: 0.5rem;">No Active Applications</div>
                <p style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 0;">
                    When you apply for jobs or save opportunities, your pipeline funnel will appear here.
                </p>
            </div>
            """)
        st.page_link("pages/10_📋_Application_Tracker.py", label="Go to Application Tracker →")

    st.subheader("High-Impact Skills to Learn")
    if recs:
        missing_freq = {}
        for r in recs:
            for s in r.get("missing_required_skills", []):
                missing_freq[s] = missing_freq.get(s, 0) + 1
        sorted_gaps = sorted(missing_freq.items(), key=lambda x: x[1], reverse=True)[:4]
        if sorted_gaps:
            for skill, freq in sorted_gaps:
                pct = int((freq / len(recs)) * 100)
                render_html(f"""
                <div style="display: flex; justify-content: space-between; font-size: 0.85rem; font-weight: 600; color: #0F172A; margin-bottom: 3px;">
                    <span>{skill}</span>
                    <span style="color: #64748B;">{pct}% of matches</span>
                </div>
                """)
                st.progress(pct / 100.0)
            st.page_link("pages/8_🎯_Skill_Gap_Analysis.py", label="Detailed Learning Roadmap →")
        else:
            st.success("Your stack covers 100% of the required skills in your top matches!")
