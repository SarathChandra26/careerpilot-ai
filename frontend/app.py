import streamlit as st
from components.ui_theme import inject_custom_theme, render_html
from components.sidebar import render_sidebar
from utils.api_client import api

st.set_page_config(
    page_title="CareerPilot — AI Career Intelligence",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)

inject_custom_theme()
render_sidebar()

candidate = st.session_state.get("candidate")
candidate_id = st.session_state.get("candidate_id")
user_name = candidate.get("full_name", "Alex").split()[0] if candidate else "Alex"

# Hero Header Banner
render_html(f"""
<div class="cp-card-hero">
    <div style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; opacity: 0.85; margin-bottom: 0.4rem;">
        Autonomous Career Copilot
    </div>
    <h1 style="font-size: 2.2rem; font-weight: 800; margin-bottom: 0.5rem; letter-spacing: -0.03em;">
        Welcome back, {user_name}
    </h1>
    <p style="font-size: 1rem; opacity: 0.9; max-width: 680px; line-height: 1.5; margin: 0;">
        Your personal career engine has analyzed your verified competencies and refreshed your top recommendations across 250+ vetted roles.
    </p>
</div>
""")

# Core KPIs Row
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

jobs_res = api.get_jobs(page_size=1)
total_jobs = jobs_res.get("total", 0)

saved_jobs = api.get_saved_jobs(candidate_id) if candidate_id else []
apps = api.get_applications(candidate_id) if candidate_id else []
comp_score = candidate.get("completeness_score", 0.0) if candidate else 0.0

with kpi1:
    render_html(f"""
    <div class="cp-stat-card">
        <div>
            <div class="cp-stat-label">Active Catalog</div>
            <div class="cp-stat-value">{total_jobs:,}</div>
        </div>
        <div class="cp-stat-sub">Indexed & verified</div>
    </div>
    """)

with kpi2:
    render_html(f"""
    <div class="cp-stat-card">
        <div>
            <div class="cp-stat-label">Profile Strength</div>
            <div class="cp-stat-value">{comp_score:.0f}%</div>
        </div>
        <div class="cp-stat-sub">High match potential</div>
    </div>
    """)

with kpi3:
    render_html(f"""
    <div class="cp-stat-card">
        <div>
            <div class="cp-stat-label">Saved Opportunities</div>
            <div class="cp-stat-value">{len(saved_jobs)}</div>
        </div>
        <div style="font-size: 0.8rem; font-weight: 500; color: #64748B; margin-top: 0.25rem;">Bookmarked</div>
    </div>
    """)

with kpi4:
    render_html(f"""
    <div class="cp-stat-card">
        <div>
            <div class="cp-stat-label">Pipeline Active</div>
            <div class="cp-stat-value">{len(apps)}</div>
        </div>
        <div style="font-size: 0.8rem; font-weight: 500; color: #6366F1; margin-top: 0.25rem;">In flight</div>
    </div>
    """)

st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

# Top Matches Section
if candidate_id:
    st.subheader("Top Matches for Your Stack")
    st.caption("Computed using transparent multi-factor scoring against your verified skills and preferred work modes.")

    recs_res = api.get_recommendations(candidate_id, limit=3, min_score=40.0)
    recs = recs_res.get("recommendations", [])

    if recs:
        r_cols = st.columns(len(recs))
        for idx, rec in enumerate(recs):
            with r_cols[idx]:
                job_obj = rec.get("job") or {}
                job_id = job_obj.get("id") or rec.get("job_id", f"home_job_{idx}")
                title = job_obj.get("title") or rec.get("title", "Opportunity")
                company = job_obj.get("company") or rec.get("company", "Company")
                location = job_obj.get("location") or rec.get("location", "Remote")
                work_mode = job_obj.get("work_mode") or rec.get("work_mode", "Remote")
                sal_min = job_obj.get("salary_min")
                sal_max = job_obj.get("salary_max")
                sal_text = f"${sal_min:,} - ${sal_max:,}" if sal_min and sal_max else "Competitive"
                matched = rec.get("matched_required_skills", []) + rec.get("matched_preferred_skills", [])
                
                initials = "".join([w[0] for w in company.split()[:2]]).upper() or "CO"
                score = rec.get("overall_score", 0.0)
                score_color = "#059669" if score >= 75 else "#4F46E5" if score >= 55 else "#D97706"
                badge_bg = "#ECFDF5" if score >= 75 else "#EEF2FF" if score >= 55 else "#FFFBEB"

                with st.container(border=True):
                    render_html(f"""
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem;">
                            <div style="display: flex; align-items: center;">
                                <div class="cp-avatar">{initials}</div>
                                <div>
                                    <div style="font-weight: 700; font-size: 1.05rem; color: #0F172A; line-height: 1.2;">{title}</div>
                                    <div style="font-size: 0.85rem; color: #64748B; font-weight: 500;">{company}</div>
                                </div>
                            </div>
                            <span style="background: {badge_bg}; color: {score_color}; font-weight: 700; font-size: 0.8rem; padding: 3px 8px; border-radius: 9999px;">
                                {score:.0f}%
                            </span>
                        </div>
                        <div style="margin-bottom: 0.75rem;">
                            <span class="cp-badge cp-badge-neutral">{work_mode}</span>
                            <span class="cp-badge cp-badge-neutral">{location}</span>
                            <span class="cp-badge cp-badge-neutral">{sal_text}</span>
                        </div>
                        <div style="font-size: 0.8rem; color: #475569; margin-bottom: 0.5rem;">
                            <strong style="color: #0F172A;">Core Match:</strong> {', '.join(matched[:3]) if matched else 'None'}
                        </div>
                    </div>
                    """)
                    if st.button("Explore Opportunity →", key=f"home_view_{job_id}_{idx}", use_container_width=True):
                        st.session_state["target_gap_job_id"] = job_id
                        st.switch_page("pages/8_🎯_Skill_Gap_Analysis.py")

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# Grid of Core Hub Features
st.subheader("Career Tools & Workflows")

f_col1, f_col2, f_col3 = st.columns(3)

with f_col1:
    with st.container(border=True):
        render_html("""
        <div style="font-weight: 700; font-size: 1.05rem; color: #0F172A; margin-bottom: 0.35rem;">AI Career Assistant</div>
        <p style="font-size: 0.875rem; color: #64748B; line-height: 1.45; margin-bottom: 0.75rem;">
            Natural conversation backed by real tool execution. Ask to discover remote internships, analyze skill gaps, and save jobs.
        </p>
        """)
        st.page_link("pages/4_💬_AI_Career_Assistant.py", label="Open Assistant", use_container_width=True)

with f_col2:
    with st.container(border=True):
        render_html("""
        <div style="font-weight: 700; font-size: 1.05rem; color: #0F172A; margin-bottom: 0.35rem;">Skill Gap Roadmap</div>
        <p style="font-size: 0.875rem; color: #64748B; line-height: 1.45; margin-bottom: 0.75rem;">
            Benchmark your stack against any job in the catalogue. Receive clear learning priorities and project suggestions.
        </p>
        """)
        st.page_link("pages/8_🎯_Skill_Gap_Analysis.py", label="Audit Skill Gaps", use_container_width=True)

with f_col3:
    with st.container(border=True):
        render_html("""
        <div style="font-weight: 700; font-size: 1.05rem; color: #0F172A; margin-bottom: 0.35rem;">Interview Preparation</div>
        <p style="font-size: 0.875rem; color: #64748B; line-height: 1.45; margin-bottom: 0.75rem;">
            Role-tailored technical problem sets, project defense questions, and STAR behavioral frameworks for your target job.
        </p>
        """)
        st.page_link("pages/9_💡_Interview_Preparation.py", label="Generate Prep Kit", use_container_width=True)

f_col4, f_col5, f_col6 = st.columns(3)

with f_col4:
    with st.container(border=True):
        render_html("""
        <div style="font-weight: 700; font-size: 1.05rem; color: #0F172A; margin-bottom: 0.35rem;">Resume Parsing</div>
        <p style="font-size: 0.875rem; color: #64748B; line-height: 1.45; margin-bottom: 0.75rem;">
            Upload PDF or DOCX documents. Automatically extract technical competencies, degrees, and update your profile.
        </p>
        """)
        st.page_link("pages/3_📄_Resume_Analysis.py", label="Upload Resume", use_container_width=True)

with f_col5:
    with st.container(border=True):
        render_html("""
        <div style="font-weight: 700; font-size: 1.05rem; color: #0F172A; margin-bottom: 0.35rem;">Job Search & Catalog</div>
        <p style="font-size: 0.875rem; color: #64748B; line-height: 1.45; margin-bottom: 0.75rem;">
            Explore 250+ curated vacancies with instant profile compatibility scoring and multi-faceted filtering.
        </p>
        """)
        st.page_link("pages/5_🔍_Job_Search.py", label="Search Jobs", use_container_width=True)

with f_col6:
    with st.container(border=True):
        render_html("""
        <div style="font-weight: 700; font-size: 1.05rem; color: #0F172A; margin-bottom: 0.35rem;">Application Pipeline</div>
        <p style="font-size: 0.875rem; color: #64748B; line-height: 1.45; margin-bottom: 0.75rem;">
            Track applications from Saved to Offer Received. Set deadlines, interview tasks, and follow-up notes.
        </p>
        """)
        st.page_link("pages/10_📋_Application_Tracker.py", label="Track Applications", use_container_width=True)
