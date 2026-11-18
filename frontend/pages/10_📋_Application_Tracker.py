import streamlit as st
from components.ui_theme import inject_custom_theme, render_html
from components.sidebar import render_sidebar
from utils.api_client import api

st.set_page_config(page_title="Application Tracker — CareerPilot", page_icon="🧭", layout="wide")
inject_custom_theme()
render_sidebar()

candidate = st.session_state.get("candidate")
candidate_id = st.session_state.get("candidate_id")

if not candidate:
    st.warning("Please select or initialize an active candidate in the sidebar.")
    st.stop()

st.title("Application Tracker")
st.markdown("Manage your job application pipeline, interview schedule, and follow-up checklists in one place.")

tab_pipeline, tab_tasks, tab_add = st.tabs([
    "Pipeline Overview",
    "Action Checklist",
    "Track New Application"
])

applications = api.get_applications(candidate_id)
tasks = api.get_tasks(candidate_id)

stages = ["Interested", "Saved", "Preparing", "Applied", "Interview Scheduled", "Offer Received", "Rejected"]

# TAB 1: Pipeline View
with tab_pipeline:
    m_cols = st.columns(len(stages))
    stage_apps = {s: [] for s in stages}
    for app in applications:
        stg = app.get("status", "Interested")
        stage_apps.setdefault(stg, []).append(app)
        
    for i, s in enumerate(stages):
        with m_cols[i]:
            count = len(stage_apps.get(s, []))
            render_html(f"""
            <div class="cp-stat-card" style="padding: 0.75rem 0.85rem; text-align: center;">
                <div style="font-size: 0.7rem; font-weight: 700; color: #64748B; text-transform: uppercase;">{s}</div>
                <div style="font-size: 1.4rem; font-weight: 800; color: {'#4F46E5' if count > 0 else '#94A3B8'};">{count}</div>
            </div>
            """)

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    if applications:
        for app in applications:
            job = app.get("job", {})
            app_id = app.get("id")
            current_status = app.get("status", "Interested")
            company = job.get("company", "Company")
            init = "".join([w[0] for w in company.split()[:2]]).upper() or "CO"

            with st.container(border=True):
                render_html(f"""
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
                    <div style="display: flex; align-items: flex-start;">
                        <div class="cp-avatar">{init}</div>
                        <div>
                            <div style="font-weight: 700; font-size: 1.15rem; color: #0F172A;">{job.get('title', 'Unknown Job')}</div>
                            <div style="font-size: 0.875rem; color: #64748B;">{company} · {job.get('location', '')}</div>
                        </div>
                    </div>
                    <span class="cp-badge cp-badge-brand" style="font-size: 0.85rem; padding: 4px 10px;">
                        {current_status}
                    </span>
                </div>
                """)

                c1, c2 = st.columns([3, 1])
                with c1:
                    if app.get("notes"):
                        render_html(f"<div style='font-size: 0.85rem; color: #475569;'><strong>Notes:</strong> {app.get('notes')}</div>")
                    if app.get("applied_at"):
                        st.caption(f"Applied date: {app.get('applied_at')[:10]}")
                with c2:
                    curr_idx = stages.index(current_status) if current_status in stages else 0
                    new_status = st.selectbox(
                        "Update Status",
                        stages,
                        index=curr_idx,
                        key=f"status_sel_{app_id}",
                        label_visibility="collapsed"
                    )
                    if new_status != current_status:
                        api.update_application(app_id, {"status": new_status})
                        st.toast(f"Updated status to {new_status}!")
                        st.rerun()

                del_col, _ = st.columns([1, 4])
                with del_col:
                    if st.button("Delete", key=f"del_app_{app_id}", type="secondary", use_container_width=True):
                        api.delete_application(app_id)
                        st.toast("Application removed from tracker.")
                        st.rerun()
    else:
        st.info("No applications in pipeline. You can add one below or save jobs from Recommendations.")

# TAB 2: Task Checklist
with tab_tasks:
    col_t1, col_t2 = st.columns([3, 2])
    with col_t1:
        st.subheader("Action Checklist")
        if tasks:
            for t in tasks:
                t_id = t.get("id")
                is_done = t.get("is_completed", False)
                prio = t.get("priority", "medium").lower()
                prio_class = "cp-badge-danger" if prio == "high" else "cp-badge-warning" if prio == "medium" else "cp-badge-neutral"

                with st.container(border=True):
                    tc1, tc2 = st.columns([4, 1])
                    with tc1:
                        render_html(f"""
                        <div>
                            <span style="font-weight: 700; font-size: 0.95rem; {'text-decoration: line-through; color: #94A3B8;' if is_done else 'color: #0F172A;'}">
                                {t.get('title')}
                            </span>
                            <span class="cp-badge {prio_class}" style="margin-left: 0.4rem;">{prio.capitalize()}</span>
                            {f"<div style='font-size: 0.825rem; color: #64748B; margin-top: 3px;'>{t.get('description')}</div>" if t.get('description') else ''}
                        </div>
                        """)
                    with tc2:
                        chk = st.checkbox("Done", value=is_done, key=f"chk_{t_id}")
                        if chk != is_done:
                            api.update_task(t_id, {"is_completed": chk})
                            st.rerun()
        else:
            st.info("No preparation tasks logged yet.")

    with col_t2:
        st.subheader("Add Action Item")
        with st.form("new_task_form"):
            t_title = st.text_input("Task Title", placeholder="e.g. Tailor resume for DeepMind AI Intern")
            t_desc = st.text_area("Description / Details", placeholder="Highlight PyTorch and agentic tools experience")
            t_priority = st.selectbox("Priority Level", ["high", "medium", "low"], index=1)
            
            jobs_res = api.get_jobs(page_size=30)
            job_items = jobs_res.get("items", [])
            job_map = {j["id"]: f"{j['title']} · {j['company']}" for j in job_items}
            job_options = ["None"] + list(job_map.keys())
            sel_job = st.selectbox("Linked Vacancy (Optional)", job_options, format_func=lambda x: job_map.get(x, x))
            
            sub_task = st.form_submit_button("Create Action Item", type="primary")
            if sub_task and t_title:
                api.create_task(candidate_id, {
                    "job_id": None if sel_job == "None" else sel_job,
                    "title": t_title,
                    "description": t_desc,
                    "priority": t_priority,
                    "task_type": "preparation"
                })
                st.toast("Task created!")
                st.rerun()

# TAB 3: Add Application
with tab_add:
    st.subheader("Track a Job Application")
    jobs_res = api.get_jobs(page_size=100)
    job_items = jobs_res.get("items", [])
    if job_items:
        job_map = {j["id"]: f"{j['title']} · {j['company']} ({j['work_mode']})" for j in job_items}
        with st.form("add_app_form"):
            app_job_id = st.selectbox("Select Target Vacancy", list(job_map.keys()), format_func=lambda x: job_map.get(x, x))
            app_stage = st.selectbox("Initial Pipeline Stage", stages, index=3) # Default 'Applied'
            app_notes = st.text_area("Notes & Details", placeholder="Applied via referral on company careers page...")
            
            sub_app = st.form_submit_button("Track Application", type="primary")
            if sub_app:
                api.create_application(candidate_id, {
                    "job_id": app_job_id,
                    "status": app_stage,
                    "notes": app_notes
                })
                st.toast("Application tracked successfully!")
                st.rerun()
    else:
        st.warning("No jobs available in the catalogue to track.")
