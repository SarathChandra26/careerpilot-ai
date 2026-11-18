import streamlit as st
from components.ui_theme import inject_custom_theme, render_html
from components.sidebar import render_sidebar
from utils.api_client import api

st.set_page_config(page_title="My Profile — CareerPilot", page_icon="🧭", layout="wide")
inject_custom_theme()
render_sidebar()

candidate = st.session_state.get("candidate")
candidate_id = st.session_state.get("candidate_id")

if not candidate:
    st.warning("No candidate selected. Please create a profile below.")
    with st.form("new_cand_form"):
        st.subheader("Create Candidate Profile")
        name = st.text_input("Full Name", value="Alex Rivera")
        email = st.text_input("Email", value="alex.rivera@example.com")
        phone = st.text_input("Phone", value="+1 (555) 234-5678")
        edu = st.text_input("Education", value="B.S. in Computer Science")
        deg = st.text_input("Degree", value="Bachelor's Degree")
        exp_years = st.number_input("Years of Experience", min_value=0.0, max_value=40.0, value=1.0, step=0.5)
        exp_lvl = st.selectbox("Seniority Level", ["Internship", "Entry-Level", "Mid-Level", "Senior", "Lead"], index=0)
        submitted = st.form_submit_button("Create Profile", type="primary")
        if submitted:
            new_cand = api.create_candidate({
                "full_name": name,
                "email": email,
                "phone": phone,
                "education": edu,
                "degree": deg,
                "experience_years": exp_years,
                "experience_level": exp_lvl,
                "preferred_roles": ["AI Engineer", "Python Developer"],
                "preferred_locations": ["Remote"],
                "preferred_work_mode": "Remote",
                "career_interests": ["Machine Learning", "Large Language Models"]
            })
            if new_cand:
                st.session_state["candidate"] = new_cand
                st.session_state["candidate_id"] = new_cand["id"]
                st.success("Candidate created successfully!")
                st.rerun()
    st.stop()

st.title("Candidate Profile")
st.markdown("Manage your verified technical competencies, education, and career preferences.")

tab_overview, tab_skills, tab_prefs, tab_create = st.tabs([
    "Personal & Education",
    "Verified Skills",
    "Search Preferences",
    "New Profile"
])

# TAB 1: Personal Details
with tab_overview:
    with st.form("edit_details_form"):
        st.subheader("Personal Information")
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Full Name", value=candidate.get("full_name", ""))
            email = st.text_input("Email (Account Identifier)", value=candidate.get("email", ""), disabled=True)
            phone = st.text_input("Phone Number", value=candidate.get("phone", "") or "")
        with col2:
            education = st.text_input("Institution / University", value=candidate.get("education", "") or "")
            degree = st.text_input("Degree Level", value=candidate.get("degree", "") or "")
            col_exp1, col_exp2 = st.columns(2)
            with col_exp1:
                exp_years = st.number_input("Years of Experience", min_value=0.0, max_value=40.0, value=float(candidate.get("experience_years") or 0.0), step=0.5)
            with col_exp2:
                exp_lvl_options = ["Internship", "Entry-Level", "Mid-Level", "Senior", "Lead"]
                current_lvl = candidate.get("experience_level", "Internship")
                lvl_idx = exp_lvl_options.index(current_lvl) if current_lvl in exp_lvl_options else 0
                exp_level = st.selectbox("Seniority Tier", exp_lvl_options, index=lvl_idx)

        update_submitted = st.form_submit_button("Save Personal Information", type="primary")
        if update_submitted:
            updated = api.update_candidate(candidate_id, {
                "full_name": full_name,
                "phone": phone,
                "education": education,
                "degree": degree,
                "experience_years": exp_years,
                "experience_level": exp_level
            })
            if updated:
                st.session_state["candidate"] = updated
                st.toast("Profile updated successfully!")
                st.rerun()

# TAB 2: Skills
with tab_skills:
    st.subheader("Verified Competencies")
    skills = candidate.get("skills", [])

    if skills:
        grouped = {}
        for s in skills:
            cat = s.get("category", "General")
            grouped.setdefault(cat, []).append(s)

        for cat, sk_list in grouped.items():
            render_html(f"<div style='font-size: 0.85rem; font-weight: 700; text-transform: uppercase; color: #64748B; margin: 0.75rem 0 0.35rem 0;'>{cat}</div>")
            cols = st.columns(min(len(sk_list), 4))
            for i, sk in enumerate(sk_list):
                c_idx = i % 4
                with cols[c_idx]:
                    with st.container(border=True):
                        render_html(f"""
                        <div style="font-weight: 700; font-size: 0.95rem; color: #0F172A;">{sk.get('skill_name')}</div>
                        <span class="cp-badge cp-badge-brand" style="margin-top: 3px;">{sk.get('proficiency', 'Intermediate')}</span>
                        """)
                        if st.button("Remove", key=f"del_sk_{sk.get('id')}", type="secondary"):
                            api.remove_skill(candidate_id, sk.get('id'))
                            cand_refreshed = api.get_candidate(candidate_id)
                            st.session_state["candidate"] = cand_refreshed
                            st.rerun()
    else:
        st.info("No skills registered yet. Add some below or upload your resume.")

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    with st.form("add_skill_form"):
        st.subheader("Add Competency")
        sk_col1, sk_col2, sk_col3 = st.columns([2, 2, 2])
        with sk_col1:
            new_skill_name = st.text_input("Skill Name", placeholder="e.g. PyTorch, Docker, Kubernetes")
        with sk_col2:
            new_skill_cat = st.selectbox("Category", ["Programming", "AI/ML", "Frameworks", "Databases", "Cloud & DevOps", "Tools", "General"])
        with sk_col3:
            new_skill_prof = st.selectbox("Proficiency", ["Beginner", "Intermediate", "Advanced", "Expert"], index=1)

        add_btn = st.form_submit_button("Add Skill to Profile", type="primary")
        if add_btn and new_skill_name:
            api.add_skill(candidate_id, new_skill_name.strip(), new_skill_cat, new_skill_prof)
            cand_refreshed = api.get_candidate(candidate_id)
            st.session_state["candidate"] = cand_refreshed
            st.toast(f"Added {new_skill_name}!")
            st.rerun()

# TAB 3: Preferences
with tab_prefs:
    with st.form("edit_prefs_form"):
        st.subheader("Job Search Criteria")
        
        pref_roles_str = st.text_input("Target Roles (comma-separated)", value=", ".join(candidate.get("preferred_roles", [])))
        pref_locs_str = st.text_input("Preferred Locations (comma-separated)", value=", ".join(candidate.get("preferred_locations", [])))
        
        wm_options = ["Remote", "Hybrid", "On-site", "Any"]
        curr_wm = candidate.get("preferred_work_mode", "Remote")
        wm_idx = wm_options.index(curr_wm) if curr_wm in wm_options else 0
        pref_wm = st.selectbox("Preferred Work Mode", wm_options, index=wm_idx)
        
        c_interests_str = st.text_input("Career Domains & Interests (comma-separated)", value=", ".join(candidate.get("career_interests", [])))
        
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            sal_min = st.number_input("Minimum Base Salary Expectation ($)", min_value=0, value=int(candidate.get("salary_min_expectation") or 0), step=5000)
        with col_s2:
            sal_max = st.number_input("Target Salary Expectation ($)", min_value=0, value=int(candidate.get("salary_max_expectation") or 0), step=5000)

        save_prefs = st.form_submit_button("Save Search Preferences", type="primary")
        if save_prefs:
            roles_list = [r.strip() for r in pref_roles_str.split(",") if r.strip()]
            locs_list = [l.strip() for l in pref_locs_str.split(",") if l.strip()]
            interests_list = [i.strip() for i in c_interests_str.split(",") if i.strip()]
            
            updated = api.update_candidate(candidate_id, {
                "preferred_roles": roles_list,
                "preferred_locations": locs_list,
                "preferred_work_mode": pref_wm,
                "career_interests": interests_list,
                "salary_min_expectation": sal_min if sal_min > 0 else None,
                "salary_max_expectation": sal_max if sal_max > 0 else None,
            })
            if updated:
                st.session_state["candidate"] = updated
                st.toast("Preferences saved!")
                st.rerun()

# TAB 4: Create Profile
with tab_create:
    st.subheader("Create Secondary Profile")
    st.caption("You can maintain distinct candidate personas to test different target roles or seniority levels.")
    with st.form("create_extra_cand"):
        c_name = st.text_input("Full Name", value="Jordan Lee")
        c_email = st.text_input("Email", value="jordan.lee@example.com")
        c_phone = st.text_input("Phone", value="+1 (555) 987-6543")
        c_roles = st.text_input("Target Roles", value="Data Engineer, Backend Developer")
        c_lvl = st.selectbox("Seniority", ["Internship", "Entry-Level", "Mid-Level", "Senior"], index=2)
        c_btn = st.form_submit_button("Create Persona", type="primary")
        if c_btn and c_name and c_email:
            res = api.create_candidate({
                "full_name": c_name,
                "email": c_email,
                "phone": c_phone,
                "preferred_roles": [r.strip() for r in c_roles.split(",") if r.strip()],
                "experience_level": c_lvl,
                "preferred_work_mode": "Remote",
                "career_interests": ["Big Data", "Distributed Systems"]
            })
            if res:
                st.session_state["candidate"] = res
                st.session_state["candidate_id"] = res["id"]
                st.toast(f"Profile for {c_name} created and activated!")
                st.rerun()
