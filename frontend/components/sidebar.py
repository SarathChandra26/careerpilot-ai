import streamlit as st
from components.ui_theme import render_html
from utils.api_client import api

def render_sidebar():
    with st.sidebar:
        # SaaS Header with custom badge
        render_html("""
        <div style="padding: 0.5rem 0 1rem 0;">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center; gap: 9px;">
                    <div style="width: 28px; height: 28px; border-radius: 8px; background: linear-gradient(135deg, #4F46E5, #6366F1); display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 15px; color: #FFFFFF;">
                        CP
                    </div>
                    <span style="font-weight: 700; font-size: 1.15rem; letter-spacing: -0.025em; color: #FFFFFF;">CareerPilot</span>
                </div>
                <span style="font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; background: rgba(99, 102, 241, 0.18); color: #A5B4FC; padding: 2px 7px; border-radius: 9999px; border: 1px solid rgba(99, 102, 241, 0.3);">
                    v1.0
                </span>
            </div>
        </div>
        """)

        st.divider()

        # Session State for Candidate
        if "candidate" not in st.session_state or st.session_state["candidate"] is None:
            active_cand = api.get_active_candidate()
            if active_cand:
                st.session_state["candidate"] = active_cand
                st.session_state["candidate_id"] = active_cand["id"]

        candidate = st.session_state.get("candidate")

        if candidate:
            name = candidate.get("full_name", "Alex Rivera")
            initials = "".join([part[0] for part in name.split()[:2]]).upper() or "CP"
            roles = candidate.get("preferred_roles", [])
            primary_role = roles[0] if roles else "Candidate"
            comp = candidate.get("completeness_score", 0.0)

            render_html(f"""
            <div style="background: rgba(255, 255, 255, 0.04); border: 1px solid #1E293B; border-radius: 12px; padding: 1rem; margin-bottom: 0.85rem;">
                <div style="display: flex; align-items: center; gap: 11px; margin-bottom: 0.75rem;">
                    <div style="width: 38px; height: 38px; border-radius: 10px; background: #334155; color: #F8FAFC; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.95rem; border: 1px solid #475569;">
                        {initials}
                    </div>
                    <div style="overflow: hidden;">
                        <div style="font-weight: 700; font-size: 0.92rem; color: #FFFFFF; white-space: nowrap; text-overflow: ellipsis; overflow: hidden;">{name}</div>
                        <div style="font-size: 0.75rem; color: #94A3B8; font-weight: 500;">{primary_role}</div>
                    </div>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.75rem; color: #94A3B8; margin-bottom: 4px;">
                    <span>Profile Strength</span>
                    <span style="font-weight: 600; color: #CBD5E1;">{comp:.0f}%</span>
                </div>
            </div>
            """)
            st.progress(min(1.0, max(0.0, comp / 100.0)))

            # Candidate Switcher (if multiple candidates exist)
            candidates_list = api.list_candidates()
            if len(candidates_list) > 1:
                cand_names = {c["id"]: c["full_name"] for c in candidates_list}
                current_id = candidate["id"]
                cand_ids = list(cand_names.keys())
                curr_idx = cand_ids.index(current_id) if current_id in cand_ids else 0
                selected_id = st.selectbox(
                    "Profile",
                    options=cand_ids,
                    index=curr_idx,
                    format_func=lambda x: cand_names.get(x, x),
                    key="sidebar_cand_switcher"
                )
                if selected_id != current_id:
                    cand_obj = api.get_candidate(selected_id)
                    if cand_obj:
                        st.session_state["candidate"] = cand_obj
                        st.session_state["candidate_id"] = cand_obj["id"]
                        st.rerun()

            if st.button("Sync Profile", use_container_width=True):
                cand_obj = api.get_candidate(candidate["id"])
                if cand_obj:
                    st.session_state["candidate"] = cand_obj
                    st.rerun()
        else:
            st.warning("No candidate profile loaded.")
            if st.button("Initialize Profile", use_container_width=True):
                cand = api.get_active_candidate()
                if cand:
                    st.session_state["candidate"] = cand
                    st.session_state["candidate_id"] = cand["id"]
                    st.rerun()

        st.divider()

        # Engine Status
        health = api.get_health()
        db_ok = health.get("database_connected", False)
        llm_health = health.get("llm_service", {})
        is_fallback = llm_health.get("is_fallback", True)

        engine_label = "Local Ollama" if not is_fallback else "Deterministic Engine"
        status_color = "#10B981" if db_ok else "#EF4444"

        render_html(f"""
        <div style="font-size: 0.75rem; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em; color: #64748B; margin-bottom: 0.6rem;">
            SYSTEM
        </div>
        <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid #1E293B; border-radius: 8px; padding: 0.75rem; font-size: 0.8rem;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
                <span style="color: #94A3B8;">Database</span>
                <span style="display: flex; align-items: center; gap: 5px; color: #FFFFFF; font-weight: 600;">
                    <span style="width: 7px; height: 7px; border-radius: 50%; background: {status_color};"></span>
                    SQLite
                </span>
            </div>
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <span style="color: #94A3B8;">AI Model</span>
                <span style="color: #CBD5E1; font-weight: 500;">{engine_label}</span>
            </div>
        </div>
        """)

        st.divider()
        render_html("""
        <div style="font-size: 0.72rem; color: #64748B; text-align: center; line-height: 1.4;">
            CareerPilot AI · Local & Private<br/>
            No external API calls
        </div>
        """)
