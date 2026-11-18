import streamlit as st
import plotly.graph_objects as go
from components.ui_theme import inject_custom_theme, render_html
from components.sidebar import render_sidebar
from utils.api_client import api

st.set_page_config(page_title="Job Comparison — CareerPilot", page_icon="🧭", layout="wide")
inject_custom_theme()
render_sidebar()

candidate = st.session_state.get("candidate")
candidate_id = st.session_state.get("candidate_id")

if not candidate:
    st.warning("Please select or initialize an active candidate in the sidebar.")
    st.stop()

st.title("Job Opportunity Comparison")
st.markdown("Side-by-side multi-factor breakdown evaluating requirements, compensation, and profile fit.")

# Job Selector Row
jobs_res = api.get_jobs(page_size=50)
jobs_list = jobs_res.get("items", [])

if not jobs_list:
    st.warning("No jobs available in the catalogue to compare.")
    st.stop()

job_options = {j["id"]: f"{j['title']} · {j['company']} ({j['work_mode']})" for j in jobs_list}
job_ids = list(job_options.keys())

with st.container(border=True):
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        job_a_id = st.selectbox(
            "Opportunity A",
            options=job_ids,
            index=0,
            format_func=lambda x: job_options.get(x, x),
            key="compare_job_a"
        )
    with col_sel2:
        idx_b = 1 if len(job_ids) > 1 else 0
        job_b_id = st.selectbox(
            "Opportunity B",
            options=job_ids,
            index=idx_b,
            format_func=lambda x: job_options.get(x, x),
            key="compare_job_b"
        )

if job_a_id and job_b_id:
    job_a = api.get_job(job_a_id)
    job_b = api.get_job(job_b_id)
    
    comp_a = api.compare_job(candidate_id, job_a_id)
    comp_b = api.compare_job(candidate_id, job_b_id)

    # Comparison Cards
    c_a, c_b = st.columns(2)
    with c_a:
        score_a = comp_a.get("overall_score", 0.0) if comp_a else 0.0
        company_a = job_a.get("company", "Company A")
        init_a = "".join([w[0] for w in company_a.split()[:2]]).upper() or "CO"
        sal_a = f"${job_a.get('salary_min'):,} - ${job_a.get('salary_max'):,}" if job_a.get('salary_min') and job_a.get('salary_max') else "Competitive"
        matched_a = comp_a.get('matched_required_skills', []) + comp_a.get('matched_preferred_skills', []) if comp_a else []
        missing_a = comp_a.get('missing_required_skills', []) if comp_a else []
        score_color_a = "#059669" if score_a >= 75 else "#4F46E5" if score_a >= 55 else "#D97706"
        badge_bg_a = "#ECFDF5" if score_a >= 75 else "#EEF2FF" if score_a >= 55 else "#FFFBEB"
        
        with st.container(border=True):
            render_html(f"""
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem;">
                <div style="display: flex; align-items: center;">
                    <div class="cp-avatar">{init_a}</div>
                    <div>
                        <div style="font-weight: 700; font-size: 1.15rem; color: #0F172A;">{job_a.get('title')}</div>
                        <div style="font-size: 0.875rem; color: #64748B;">{company_a} · {job_a.get('location')}</div>
                    </div>
                </div>
                <span style="background: {badge_bg_a}; color: {score_color_a}; font-weight: 800; font-size: 1rem; padding: 4px 10px; border-radius: 9999px;">
                    {score_a:.1f}% Fit
                </span>
            </div>
            <div style="margin-bottom: 0.75rem;">
                <span class="cp-badge cp-badge-neutral">{job_a.get('work_mode')}</span>
                <span class="cp-badge cp-badge-neutral">{job_a.get('experience_level')}</span>
                <span class="cp-badge cp-badge-neutral">{sal_a}</span>
            </div>
            <div style="font-size: 0.825rem; margin-bottom: 0.5rem;">
                <div style="margin-bottom: 4px;"><strong style="color: #059669;">Matched Competencies:</strong> {', '.join(matched_a) if matched_a else 'None'}</div>
                <div style="color: #DC2626;"><strong>Missing Required:</strong> {', '.join(missing_a) if missing_a else 'None'}</div>
            </div>
            """)

    with c_b:
        score_b = comp_b.get("overall_score", 0.0) if comp_b else 0.0
        company_b = job_b.get("company", "Company B")
        init_b = "".join([w[0] for w in company_b.split()[:2]]).upper() or "CO"
        sal_b = f"${job_b.get('salary_min'):,} - ${job_b.get('salary_max'):,}" if job_b.get('salary_min') and job_b.get('salary_max') else "Competitive"
        matched_b = comp_b.get('matched_required_skills', []) + comp_b.get('matched_preferred_skills', []) if comp_b else []
        missing_b = comp_b.get('missing_required_skills', []) if comp_b else []
        score_color_b = "#059669" if score_b >= 75 else "#4F46E5" if score_b >= 55 else "#D97706"
        badge_bg_b = "#ECFDF5" if score_b >= 75 else "#EEF2FF" if score_b >= 55 else "#FFFBEB"

        with st.container(border=True):
            render_html(f"""
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem;">
                <div style="display: flex; align-items: center;">
                    <div class="cp-avatar" style="background: #1E293B;">{init_b}</div>
                    <div>
                        <div style="font-weight: 700; font-size: 1.15rem; color: #0F172A;">{job_b.get('title')}</div>
                        <div style="font-size: 0.875rem; color: #64748B;">{company_b} · {job_b.get('location')}</div>
                    </div>
                </div>
                <span style="background: {badge_bg_b}; color: {score_color_b}; font-weight: 800; font-size: 1rem; padding: 4px 10px; border-radius: 9999px;">
                    {score_b:.1f}% Fit
                </span>
            </div>
            <div style="margin-bottom: 0.75rem;">
                <span class="cp-badge cp-badge-neutral">{job_b.get('work_mode')}</span>
                <span class="cp-badge cp-badge-neutral">{job_b.get('experience_level')}</span>
                <span class="cp-badge cp-badge-neutral">{sal_b}</span>
            </div>
            <div style="font-size: 0.825rem; margin-bottom: 0.5rem;">
                <div style="margin-bottom: 4px;"><strong style="color: #059669;">Matched Competencies:</strong> {', '.join(matched_b) if matched_b else 'None'}</div>
                <div style="color: #DC2626;"><strong>Missing Required:</strong> {', '.join(missing_b) if missing_b else 'None'}</div>
            </div>
            """)

    # Dimensional Chart
    st.subheader("Comparative Compatibility Dimensions")
    categories = ['Required Skills', 'Preferred Skills', 'Experience Level', 'Role Fit', 'Work Mode', 'Location']
    
    bk_a = comp_a.get("breakdown", {}) if comp_a else {}
    bk_b = comp_b.get("breakdown", {}) if comp_b else {}
    weights_a = [
        bk_a.get("required_skill_overlap_ratio", 0) * 100,
        bk_a.get("preferred_skill_overlap_ratio", 0) * 100,
        100 if comp_a.get("experience_compatible") else 40,
        bk_a.get("role_relevance_ratio", 0) * 100,
        100 if comp_a.get("work_mode_compatible") else 30,
        100 if comp_a.get("location_compatible") else 30,
    ] if comp_a else [0]*6

    weights_b = [
        bk_b.get("required_skill_overlap_ratio", 0) * 100,
        bk_b.get("preferred_skill_overlap_ratio", 0) * 100,
        100 if comp_b.get("experience_compatible") else 40,
        bk_b.get("role_relevance_ratio", 0) * 100,
        100 if comp_b.get("work_mode_compatible") else 30,
        100 if comp_b.get("location_compatible") else 30,
    ] if comp_b else [0]*6

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=categories,
        y=weights_a,
        name=f"{job_a.get('title')}",
        marker_color='#4F46E5',
        marker_line_width=0
    ))
    fig.add_trace(go.Bar(
        x=categories,
        y=weights_b,
        name=f"{job_b.get('title')}",
        marker_color='#10B981',
        marker_line_width=0
    ))

    fig.update_layout(
        barmode='group',
        yaxis=dict(title="Compatibility (%)", range=[0, 100], gridcolor="#F1F5F9"),
        xaxis=dict(gridcolor="rgba(0,0,0,0)"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Plus Jakarta Sans", size=12, color="#0F172A"),
        margin=dict(t=20, b=30, l=40, r=20),
        height=320,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Strategic Assessment
    diff = abs(score_a - score_b)
    higher_job = job_a if score_a >= score_b else job_b
    with st.container(border=True):
        render_html(f"""
        <div style="border-left: 4px solid #4F46E5; padding-left: 1rem;">
            <div style="font-weight: 700; font-size: 1rem; color: #0F172A; margin-bottom: 0.25rem;">
                Strategic Assessment
            </div>
            <div style="font-size: 0.875rem; color: #475569; line-height: 1.5;">
                <strong>{higher_job.get('title')} at {higher_job.get('company')}</strong> is your stronger match right now (+{diff:.1f}% higher affinity). 
                Your existing competencies fulfill a higher proportion of their non-negotiable requirements.
            </div>
        </div>
        """)
