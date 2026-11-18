import re
from typing import Dict, Any, Optional, List, Tuple

class IntentDetector:
    @staticmethod
    def extract_memories(user_message: str) -> List[Dict[str, str]]:
        extracted = []
        msg_lower = user_message.lower()

        # Work Mode preferences
        if "prefer remote" in msg_lower or "want remote" in msg_lower or "only remote" in msg_lower:
            extracted.append({
                "category": "career_preference",
                "key": "preferred_work_mode",
                "value": "Remote"
            })
        elif "prefer hybrid" in msg_lower:
            extracted.append({
                "category": "career_preference",
                "key": "preferred_work_mode",
                "value": "Hybrid"
            })
        elif "prefer on-site" in msg_lower or "prefer onsite" in msg_lower:
            extracted.append({
                "category": "career_preference",
                "key": "preferred_work_mode",
                "value": "On-site"
            })

        # Location preferences
        loc_match = re.search(r'(located in|living in|based in|move to|relocate to)\s+([A-Za-z\s]+)', user_message, re.IGNORECASE)
        if loc_match:
            loc = loc_match.group(2).strip()
            if len(loc.split()) <= 3:
                extracted.append({
                    "category": "preferred_location",
                    "key": f"location_{loc.lower()}",
                    "value": loc.title()
                })

        # Career Goal
        goal_match = re.search(r'(want to become|aiming for|target role is|looking for)\s+an?\s+([A-Za-z\s]+(engineer|developer|analyst|scientist))', user_message, re.IGNORECASE)
        if goal_match:
            role = goal_match.group(2).strip().title()
            extracted.append({
                "category": "career_goal",
                "key": f"target_role_{role.lower().replace(' ', '_')}",
                "value": f"Secure a position as {role}"
            })

        # Stated Skills
        skills_match = re.search(r'(i know|skilled in|experience in|proficient in)\s+([^.]+)', user_message, re.IGNORECASE)
        if skills_match:
            skills_chunk = skills_match.group(2)
            techs = re.split(r'[,&]|\band\b', skills_chunk)
            for t in techs:
                t_clean = t.strip()
                if 2 <= len(t_clean) <= 25 and not any(w in t_clean.lower() for w in ["job", "internship", "remote", "company"]):
                    extracted.append({
                        "category": "preferred_technology",
                        "key": f"tech_{t_clean.lower().replace(' ', '_')}",
                        "value": t_clean.title()
                    })

        return extracted

    @staticmethod
    def detect_fallback_tool(user_message: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        msg_lower = user_message.lower()

        # 1. Saved Jobs list
        if any(w in msg_lower for w in ["saved jobs", "my saved", "show saved", "view saved"]):
            return "get_saved_jobs", {}

        # 2. Save a specific Job
        if any(w in msg_lower for w in ["save this", "save job", "bookmark this", "save opportunity", "save the"]):
            return "save_job", {}

        # 3. Compare Job
        if any(w in msg_lower for w in ["compare", "suitability", "how well do i match", "match score"]):
            return "compare_job_with_candidate", {}

        # 4. Skill Gaps
        if any(w in msg_lower for w in ["missing", "skill gap", "what do i lack", "what to learn", "skills to improve"]):
            return "identify_skill_gaps", {}

        # 5. Interview Prep
        if any(w in msg_lower for w in ["interview", "questions for", "prepare for", "interview prep"]):
            return "generate_interview_questions", {}

        # 6. Tasks & Checklist
        if any(w in msg_lower for w in ["tasks", "checklist", "to-do", "todo", "action items"]):
            return "get_application_tasks", {}

        # 7. Candidate Profile
        if any(w in msg_lower for w in ["my profile", "my resume", "view profile", "my skills", "verified skills"]):
            return "get_candidate_profile", {}

        # 8. Search / Find Jobs (General discovery intent)
        if any(w in msg_lower for w in ["find", "search", "internship", "opportunities", "vacancies", "openings", "jobs", "positions"]):
            query = ""
            for role in ["ai engineer", "machine learning", "python", "data analyst", "data engineer", "software engineer", "backend", "n8n"]:
                if role in msg_lower:
                    query = role.title()
                    break

            work_mode = None
            if "remote" in msg_lower:
                work_mode = "Remote"
            elif "hybrid" in msg_lower:
                work_mode = "Hybrid"
            elif "on-site" in msg_lower or "onsite" in msg_lower:
                work_mode = "On-site"

            exp_level = "Internship" if "intern" in msg_lower else None

            return "search_jobs", {
                "query": query or None,
                "work_mode": work_mode,
                "experience_level": exp_level,
                "limit": 5,
            }

        return None
