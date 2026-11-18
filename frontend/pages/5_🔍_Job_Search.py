import streamlit as st
from components.ui_theme import inject_custom_theme, render_html
from components.sidebar import render_sidebar
from utils.api_client import api

st.set_page_config(page_title="Job Search — CareerPilot", page_icon="🧭", layout="wide")
inject_custom_theme()
render_sidebar()

candidate = st.session_state.get("candidate")
candidate_id = st.session_state.get("candidate_id")

st.title("Job Catalogue")
st.markdown("Browse and filter 250+ curated technology vacancies. Each posting includes real-time match scoring against your profile.")

# Filter Bar Card
with st.container(border=True):
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_query = st.text_input("Keywords or Title", placeholder="e.g. AI Engineer, Python, Distributed Systems")
    with col2:
        categories = [
            "All Categories",
            "AI Engineer",
            "Machine Learning Engineer",
            "Python Developer",
            "Data Analyst",
            "Data Engineer",
            "Software Engineer",
            "Backend Developer",
            "Automation Engineer",
            "Business Analyst",
            "Product Support Engineer"
        ]
        sel_cat = st.selectbox("Category", categories)
        role_category = None if sel_cat == "All Categories" else sel_cat
    with col3:
        work_modes = ["All Modes", "Remote", "Hybrid", "On-site"]
        sel_wm = st.selectbox("Work Mode", work_modes)
        work_mode = None if sel_wm == "All Modes" else sel_wm

    col4, col5, col6 = st.columns(3)
    with col4:
        exp_levels = ["All Seniorities", "Internship", "Entry-Level", "Mid-Level", "Senior", "Lead"]
        sel_exp = st.selectbox("Seniority Level", exp_levels)
        exp_level = None if sel_exp == "All Seniorities" else sel_exp
    with col5:
        location_filter = st.text_input("Location", placeholder="e.g. Remote, San Francisco, New York")
        location = location_filter.strip() if location_filter.strip() else None
    with col6:
        min_salary = st.number_input("Minimum Base Salary ($)", min_value=0, max_value=250000, value=0, step=10000)
        salary_param = min_salary if min_salary > 0 else None

# Pagination State
if "search_page" not in st.session_state:
    st.session_state["search_page"] = 1

page_num = st.session_state["search_page"]
page_size = 6

jobs_data = api.get_jobs(
    query=search_query,
    role_category=role_category,
    experience_level=exp_level,
    work_mode=work_mode,
    location=location,
    min_salary=salary_param,
    page=page_num,
    page_size=page_size
)

total_jobs = jobs_data.get("total", 0)
jobs_list = jobs_data.get("items", [])

# Saved Jobs Set
saved_jobs = api.get_saved_jobs(candidate_id) if candidate_id else []
saved_job_ids = {s.get("job_id") for s in saved_jobs}

render_html(f"<div style='font-size: 0.9rem; font-weight: 600; color: #475569; margin-bottom: 1rem;'>Showing {len(jobs_list)} of {total_jobs} opportunities</div>")

if jobs_list:
    for job in jobs_list:
        job_id = job.get("id")
        is_saved = job_id in saved_job_ids
        company = job.get("company", "Company")
        initials = "".join([w[0] for w in company.split()[:2]]).upper() or "CO"

        # Compare with profile
        comp = api.compare_job(candidate_id, job_id) if candidate_id else None
        score = comp.get("overall_score", 0.0) if comp else None
        sal_text = f"${job.get('salary_min'):,} - ${job.get('salary_max'):,}" if job.get('salary_min') and job.get('salary_max') else "Competitive"

        with st.container(border=True):
            render_html(f"""
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div style="display: flex; align-items: flex-start;">
                    <div class="cp-avatar">{initials}</div>
                    <div>
                        <div style="font-weight: 700; font-size: 1.15rem; color: #0F172A; margin-bottom: 2px;">{job.get('title')}</div>
                        <div style="font-size: 0.875rem; color: #64748B; font-weight: 500; margin-bottom: 6px;">
                            {company} · {job.get('location')}
                        </div>
                        <div>
                            <span class="cp-badge cp-badge-neutral">{job.get('work_mode')}</span>
                            <span class="cp-badge cp-badge-neutral">{job.get('experience_level')}</span>
                            <span class="cp-badge cp-badge-neutral">{job.get('employment_type', 'Full-time')}</span>
                            <span class="cp-badge cp-badge-neutral">{sal_text}</span>
                        </div>
                    </div>
                </div>
                {f'''
                <div style="text-align: right;">
                    <div style="font-size: 1.4rem; font-weight: 800; color: {'#059669' if score >= 75 else '#4F46E5' if score >= 55 else '#D97706'};">
                        {score:.0f}%
                    </div>
                    <div style="font-size: 0.72rem; color: #64748B; font-weight: 600; text-transform: uppercase;">Match Score</div>
                </div>
                ''' if score is not None else ''}
            </div>
            """)

            # Skills
            req_skills = [s.get("skill_name") for s in job.get("skills", []) if s.get("is_required")]
            pref_skills = [s.get("skill_name") for s in job.get("skills", []) if not s.get("is_required")]

            render_html(f"""
            <div style="margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid #F1F5F9; font-size: 0.825rem;">
                <div style="margin-bottom: 4px;">
                    <strong style="color: #0F172A;">Required Competencies:</strong> {', '.join(req_skills) if req_skills else 'None specified'}
                </div>
                {f'<div style="color: #64748B;"><strong>Preferred:</strong> {", ".join(pref_skills)}</div>' if pref_skills else ''}
            </div>
            """)

            with st.expander("Read Full Job Description"):
                st.write(job.get("description", "No description provided."))

            # Action Buttons Row
            b_col1, b_col2, b_col3, _ = st.columns([1, 1.2, 1.2, 2])
            with b_col1:
                if is_saved:
                    if st.button("Saved", key=f"unsave_{job_id}", type="secondary", use_container_width=True):
                        api.remove_saved_job(candidate_id, job_id)
                        st.toast("Removed from saved opportunities.")
                        st.rerun()
                else:
                    if st.button("Save Job", key=f"save_{job_id}", use_container_width=True):
                        if candidate_id:
                            api.save_job(candidate_id, job_id)
                            st.toast("Saved opportunity to profile!")
                            st.rerun()

            with b_col2:
                if st.button("Skill Gap Analysis", key=f"gap_{job_id}", use_container_width=True):
                    st.session_state["target_gap_job_id"] = job_id
                    st.switch_page("pages/8_🎯_Skill_Gap_Analysis.py")

            with b_col3:
                if st.button("Interview Prep Kit", key=f"prep_{job_id}", use_container_width=True):
                    st.session_state["target_interview_job_id"] = job_id
                    st.switch_page("pages/9_💡_Interview_Preparation.py")
else:
    st.info("No job postings match your active filter criteria.")

# Pagination
st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
p_col1, p_col2, p_col3 = st.columns([1, 3, 1])
with p_col1:
    if st.session_state["search_page"] > 1:
        if st.button("← Previous Page"):
            st.session_state["search_page"] -= 1
            st.rerun()
with p_col3:
    max_pages = max(1, (total_jobs + page_size - 1) // page_size)
    if st.session_state["search_page"] < max_pages:
        if st.button("Next Page →"):
            st.session_state["search_page"] += 1
            st.rerun()
