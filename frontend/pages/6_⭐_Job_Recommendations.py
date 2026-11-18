import streamlit as st
from components.ui_theme import inject_custom_theme, render_html
from components.sidebar import render_sidebar
from utils.api_client import api

st.set_page_config(page_title="Recommendations — CareerPilot", page_icon="🧭", layout="wide")
inject_custom_theme()
render_sidebar()

candidate = st.session_state.get("candidate")
candidate_id = st.session_state.get("candidate_id")

if not candidate:
    st.warning("Please select or initialize an active candidate in the sidebar.")
    st.stop()

st.title("Personalized Recommendations")
st.markdown("Roles ranked using transparent multi-factor weighting. Your feedback dynamically tunes your affinity profile.")

# Filter Bar
with st.container(border=True):
    c1, c2 = st.columns([3, 1])
    with c1:
        min_score = st.slider("Minimum Match Threshold (%)", min_value=25.0, max_value=90.0, value=35.0, step=5.0)
    with c2:
        rec_limit = st.selectbox("Display Limit", [5, 10, 15, 25], index=1)

# Fetch recommendations
with st.spinner("Calculating profile affinity across active vacancies..."):
    recs_res = api.get_recommendations(candidate_id, limit=rec_limit, min_score=min_score)
    recs = recs_res.get("recommendations", [])
    total_eval = recs_res.get("total_evaluated", 0)

render_html(f"<div style='font-size: 0.875rem; font-weight: 600; color: #64748B; margin-bottom: 1rem;'>Evaluated {total_eval} vacancies · Found {len(recs)} high-compatibility matches</div>")

# Saved jobs check
saved_jobs = api.get_saved_jobs(candidate_id)
saved_job_ids = {s.get("job_id") for s in saved_jobs}

if recs:
    for idx, rec in enumerate(recs):
        job_obj = rec.get("job") or {}
        job_id = job_obj.get("id") or rec.get("job_id", f"job_{idx}")
        title = job_obj.get("title") or rec.get("title", "Opportunity")
        company = job_obj.get("company") or rec.get("company", "Company")
        location = job_obj.get("location") or rec.get("location", "Remote")
        work_mode = job_obj.get("work_mode") or rec.get("work_mode", "Remote")
        exp_lvl = job_obj.get("experience_level") or rec.get("experience_level", "")
        sal_min = job_obj.get("salary_min")
        sal_max = job_obj.get("salary_max")
        sal_text = f"${sal_min:,} - ${sal_max:,}" if sal_min and sal_max else "Competitive"
        
        score = rec.get("overall_score", 0.0)
        is_saved = job_id in saved_job_ids
        initials = "".join([w[0] for w in company.split()[:2]]).upper() or "CO"

        score_color = "#059669" if score >= 75 else "#4F46E5" if score >= 55 else "#D97706"
        badge_bg = "#ECFDF5" if score >= 75 else "#EEF2FF" if score >= 55 else "#FFFBEB"

        matched = rec.get("matched_required_skills", []) + rec.get("matched_preferred_skills", [])
        missing_req = rec.get("missing_required_skills", [])
        missing_pref = rec.get("missing_preferred_skills", [])

        with st.container(border=True):
            render_html(f"""
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem;">
                <div style="display: flex; align-items: flex-start;">
                    <div class="cp-avatar">{initials}</div>
                    <div>
                        <div style="font-weight: 700; font-size: 1.15rem; color: #0F172A; margin-bottom: 2px;">{title}</div>
                        <div style="font-size: 0.875rem; color: #64748B; font-weight: 500; margin-bottom: 6px;">
                            {company} · {location}
                        </div>
                        <div>
                            <span class="cp-badge cp-badge-neutral">{work_mode}</span>
                            <span class="cp-badge cp-badge-neutral">{exp_lvl}</span>
                            <span class="cp-badge cp-badge-neutral">{sal_text}</span>
                        </div>
                    </div>
                </div>
                <div style="text-align: right;">
                    <span style="background: {badge_bg}; color: {score_color}; font-weight: 800; font-size: 1.1rem; padding: 4px 12px; border-radius: 9999px;">
                        {score:.1f}% Match
                    </span>
                </div>
            </div>
            
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 0.75rem 1rem; margin-bottom: 0.75rem; font-size: 0.85rem; color: #334155;">
                <strong style="color: #0F172A;">Scoring Rationale:</strong> {rec.get('explanation', '')}
            </div>

            <div style="font-size: 0.825rem; margin-bottom: 0.75rem;">
                <div style="margin-bottom: 4px;">
                    <strong style="color: #059669;">Matched Competencies:</strong> {', '.join(matched) or 'None'}
                </div>
                {f'<div style="color: #DC2626;"><strong>Missing Required Skills:</strong> {", ".join(missing_req)}</div>' if missing_req else ''}
                {f'<div style="color: #64748B;"><strong>Missing Preferred Skills:</strong> {", ".join(missing_pref)}</div>' if missing_pref else ''}
            </div>
            """)

            # Workflow Buttons
            b1, b2, b3, _ = st.columns([1, 1.2, 1.2, 2])
            with b1:
                if is_saved:
                    if st.button("Saved", key=f"rec_unsave_{job_id}_{idx}", type="secondary", use_container_width=True):
                        api.remove_saved_job(candidate_id, job_id)
                        st.toast("Removed from saved list.")
                        st.rerun()
                else:
                    if st.button("Save Job", key=f"rec_save_{job_id}_{idx}", use_container_width=True):
                        api.save_job(candidate_id, job_id)
                        st.toast("Saved opportunity to profile!")
                        st.rerun()
            with b2:
                if st.button("Skill Roadmap", key=f"rec_gap_{job_id}_{idx}", use_container_width=True):
                    st.session_state["target_gap_job_id"] = job_id
                    st.switch_page("pages/8_🎯_Skill_Gap_Analysis.py")
            with b3:
                if st.button("Interview Prep", key=f"rec_prep_{job_id}_{idx}", use_container_width=True):
                    st.session_state["target_interview_job_id"] = job_id
                    st.switch_page("pages/9_💡_Interview_Preparation.py")

            # Feedback Loop Row
            render_html("""
            <div style="border-top: 1px solid #F1F5F9; padding-top: 0.5rem; margin-top: 0.5rem; font-size: 0.78rem; font-weight: 600; color: #94A3B8;">
                TUNE RECOMMENDATIONS:
            </div>
            """)
            f1, f2, f3, f4, _ = st.columns([1, 1.1, 1.2, 1.2, 2])
            with f1:
                if st.button("Relevant", key=f"fb_rel_{job_id}_{idx}", use_container_width=True):
                    api.submit_job_feedback(candidate_id, job_id, "relevant")
                    st.toast("Marked as Relevant: +1.1x boost to similar roles")
            with f2:
                if st.button("Not Relevant", key=f"fb_not_{job_id}_{idx}", use_container_width=True):
                    api.submit_job_feedback(candidate_id, job_id, "not_relevant")
                    st.toast("Marked as Not Relevant: Demoted similar roles")
            with f3:
                if st.button("Applied", key=f"fb_app_{job_id}_{idx}", use_container_width=True):
                    api.submit_job_feedback(candidate_id, job_id, "applied")
                    api.create_application(candidate_id, {"job_id": job_id, "status": "Applied", "notes": "Added from recommendations"})
                    st.toast("Added to Application Tracker!")
            with f4:
                if st.button("Not Interested", key=f"fb_dis_{job_id}_{idx}", use_container_width=True):
                    api.submit_job_feedback(candidate_id, job_id, "not_interested")
                    st.toast("Hidden from future recommendations.")
                    st.rerun()
else:
    st.info("No recommendations match this criteria. Try lowering the minimum match threshold.")
