import json
from typing import List, Dict, Any, Tuple, Set
from app.models.candidate import Candidate
from app.models.job import Job
from app.schemas.matching import JobMatchResult, MatchBreakdown
from app.schemas.job import JobResponse, JobSkillResponse

# Standardized skill synonym mapping for robust matching
SKILL_SYNONYMS: Dict[str, str] = {
    "py": "python",
    "js": "javascript",
    "ts": "typescript",
    "ml": "machine learning",
    "dl": "deep learning",
    "nlp": "natural language processing",
    "cv": "computer vision",
    "k8s": "kubernetes",
    "postgres": "postgresql",
    "mongo": "mongodb",
    "sklearn": "scikit-learn",
    "tf": "tensorflow",
    "genai": "generative ai",
    "llms": "large language models",
    "llm": "large language models",
    "aws cloud": "aws",
    "gcp cloud": "gcp",
    "node": "node.js",
    "nodejs": "node.js",
    "fast-api": "fastapi",
}

DEFAULT_WEIGHTS = {
    "required_skills": 0.35,
    "preferred_skills": 0.15,
    "role_relevance": 0.20,
    "experience": 0.10,
    "work_mode": 0.10,
    "location": 0.05,
    "career_interests": 0.05,
}

def normalize_skill(skill: str) -> str:
    cleaned = skill.strip().lower()
    return SKILL_SYNONYMS.get(cleaned, cleaned)

class MatchingScorer:
    @classmethod
    def calculate_match(
        cls,
        candidate: Candidate,
        job: Job,
        weights: Dict[str, float] = None,
        is_saved: bool = False,
        application_status: str = None,
    ) -> JobMatchResult:
        if weights is None:
            weights = DEFAULT_WEIGHTS.copy()

        # 1. Candidate skills set
        candidate_skills_raw = [s.skill_name for s in candidate.skills] if candidate.skills else []
        candidate_skills_norm = {normalize_skill(s): s for s in candidate_skills_raw}

        # 2. Job skills
        required_job_skills: List[str] = []
        preferred_job_skills: List[str] = []
        for js in job.skills:
            if js.is_required:
                required_job_skills.append(js.skill_name)
            else:
                preferred_job_skills.append(js.skill_name)

        # 3. Match required skills
        matched_required: List[str] = []
        missing_required: List[str] = []
        for req in required_job_skills:
            norm_req = normalize_skill(req)
            if norm_req in candidate_skills_norm:
                matched_required.append(candidate_skills_norm[norm_req])
            else:
                missing_required.append(req)

        # 4. Match preferred skills
        matched_preferred: List[str] = []
        missing_preferred: List[str] = []
        for pref in preferred_job_skills:
            norm_pref = normalize_skill(pref)
            if norm_pref in candidate_skills_norm:
                matched_preferred.append(candidate_skills_norm[norm_pref])
            else:
                missing_preferred.append(pref)

        # 5. Ratios
        req_ratio = len(matched_required) / max(len(required_job_skills), 1)
        pref_ratio = (
            (len(matched_preferred) / len(preferred_job_skills))
            if preferred_job_skills
            else 1.0
        )

        # 6. Experience Compatibility
        cand_exp = candidate.experience_years or 0.0
        job_exp_min = job.experience_years_min or 0.0
        is_internship = (
            "intern" in job.title.lower()
            or "intern" in job.experience_level.lower()
            or "intern" in (candidate.experience_level or "").lower()
        )

        if is_internship:
            exp_ratio = 1.0
            exp_compatible = True
        elif cand_exp >= job_exp_min:
            exp_ratio = 1.0
            exp_compatible = True
        elif cand_exp >= max(0.0, job_exp_min - 1.0):
            exp_ratio = 0.75
            exp_compatible = True
        else:
            exp_ratio = max(0.2, round(cand_exp / max(job_exp_min, 1.0), 2))
            exp_compatible = False

        # 7. Role Relevance
        preferred_roles = json.loads(candidate.preferred_roles or "[]")
        pref_roles_lower = [r.lower() for r in preferred_roles]
        job_role_cat = (job.role_category or "").lower()
        job_title_lower = (job.title or "").lower()

        role_ratio = 0.3
        if not pref_roles_lower:
            role_ratio = 0.7  # neutral if candidate hasn't specified
        else:
            for pr in pref_roles_lower:
                if pr in job_role_cat or pr in job_title_lower or job_role_cat in pr:
                    role_ratio = 1.0
                    break
                elif any(word in job_title_lower for word in pr.split()):
                    role_ratio = max(role_ratio, 0.7)

        # 8. Work Mode Compatibility
        cand_wm = (candidate.preferred_work_mode or "Any").lower()
        job_wm = (job.work_mode or "Remote").lower()
        wm_compatible = True

        if cand_wm in ["any", "all"]:
            wm_ratio = 1.0
        elif job_wm == "remote":
            wm_ratio = 1.0  # Remote fits all preferences
        elif cand_wm == job_wm:
            wm_ratio = 1.0
        elif cand_wm == "hybrid" and job_wm == "on-site":
            wm_ratio = 0.6
            wm_compatible = False
        elif cand_wm == "on-site" and job_wm == "hybrid":
            wm_ratio = 0.7
        else:
            wm_ratio = 0.3
            wm_compatible = False

        # 9. Location Compatibility
        preferred_locations = json.loads(candidate.preferred_locations or "[]")
        pref_locs_lower = [loc.lower() for loc in preferred_locations]
        job_loc = (job.location or "").lower()
        loc_compatible = True

        if job_wm == "remote" or "remote" in job_loc:
            loc_ratio = 1.0
        elif not pref_locs_lower:
            loc_ratio = 0.8  # neutral
        elif any(loc in job_loc or job_loc in loc for loc in pref_locs_lower):
            loc_ratio = 1.0
        else:
            loc_ratio = 0.4
            loc_compatible = False

        # 10. Career Interests Compatibility
        career_interests = json.loads(candidate.career_interests or "[]")
        interests_lower = [ci.lower() for ci in career_interests]
        if not interests_lower:
            interests_ratio = 0.7
        else:
            matches = 0
            for ci in interests_lower:
                if ci in job_role_cat or ci in job_title_lower or ci in job.description.lower():
                    matches += 1
            interests_ratio = min(1.0, round(matches / max(len(interests_lower), 1), 2))

        # 11. Overall Score Weighted Calculation
        overall_score_raw = (
            weights["required_skills"] * req_ratio
            + weights["preferred_skills"] * pref_ratio
            + weights["role_relevance"] * role_ratio
            + weights["experience"] * exp_ratio
            + weights["work_mode"] * wm_ratio
            + weights["location"] * loc_ratio
            + weights["career_interests"] * interests_ratio
        )
        overall_score = round(min(100.0, max(0.0, overall_score_raw * 100)), 1)

        # 12. Explanation generation
        explanation_parts = []
        explanation_parts.append(
            f"Matches {len(matched_required)}/{len(required_job_skills)} required skills ({int(req_ratio * 100)}%)."
        )
        if preferred_job_skills:
            explanation_parts.append(
                f"Matches {len(matched_preferred)}/{len(preferred_job_skills)} preferred skills ({int(pref_ratio * 100)}%)."
            )
        if exp_compatible:
            explanation_parts.append(f"Experience aligned ({cand_exp} yrs vs {job_exp_min} req).")
        else:
            explanation_parts.append(f"Experience gap ({cand_exp} yrs vs {job_exp_min} req).")

        if wm_compatible:
            explanation_parts.append(f"Work mode compatible ({job.work_mode}).")

        explanation = " ".join(explanation_parts)

        breakdown = MatchBreakdown(
            required_skill_overlap_ratio=round(req_ratio, 2),
            preferred_skill_overlap_ratio=round(pref_ratio, 2),
            experience_compatibility_ratio=round(exp_ratio, 2),
            role_relevance_ratio=round(role_ratio, 2),
            work_mode_compatibility_ratio=round(wm_ratio, 2),
            location_compatibility_ratio=round(loc_ratio, 2),
            career_interest_ratio=round(interests_ratio, 2),
            formula_weights=weights,
        )

        job_resp = JobResponse(
            id=job.id,
            company=job.company,
            title=job.title,
            description=job.description,
            role_category=job.role_category,
            experience_level=job.experience_level,
            experience_years_min=job.experience_years_min,
            location=job.location,
            work_mode=job.work_mode,
            employment_type=job.employment_type,
            salary_min=job.salary_min,
            salary_max=job.salary_max,
            salary_currency=job.salary_currency,
            application_url=job.application_url,
            is_synthetic=job.is_synthetic,
            date_posted=job.date_posted,
            created_at=job.created_at,
            updated_at=job.updated_at,
            skills=[
                JobSkillResponse(
                    id=s.id,
                    job_id=s.job_id,
                    skill_name=s.skill_name,
                    is_required=s.is_required,
                    importance_weight=s.importance_weight,
                )
                for s in job.skills
            ],
        )

        return JobMatchResult(
            job=job_resp,
            overall_score=overall_score,
            matched_required_skills=matched_required,
            matched_preferred_skills=matched_preferred,
            missing_required_skills=missing_required,
            missing_preferred_skills=missing_preferred,
            experience_compatible=exp_compatible,
            location_compatible=loc_compatible,
            work_mode_compatible=wm_compatible,
            breakdown=breakdown,
            explanation=explanation,
            is_saved=is_saved,
            application_status=application_status,
        )
