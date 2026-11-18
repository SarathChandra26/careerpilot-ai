import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.repositories.candidate_repo import CandidateRepository
from app.repositories.job_repo import JobRepository
from app.services.llm_service import llm_service
from app.schemas.interview import InterviewResponse, InterviewQuestion

class InterviewService:
    def __init__(self, db: Session):
        self.db = db
        self.cand_repo = CandidateRepository(db)
        self.job_repo = JobRepository(db)

    def generate_interview_prep(self, candidate_id: str, job_id: str) -> InterviewResponse:
        job = self.job_repo.get_by_id(job_id)
        if not job:
            raise ValueError(f"Job with ID '{job_id}' not found.")

        candidate = self.cand_repo.get_by_id(candidate_id)
        req_skills = [s.skill_name for s in job.skills if s.is_required]
        pref_skills = [s.skill_name for s in job.skills if not s.is_required]
        cand_skills = [s.skill_name for s in candidate.skills] if candidate else []

        # Check if local Ollama LLM is available
        health = llm_service.check_health()
        if health.get("online") and health.get("model_available"):
            prompt = (
                f"You are a Senior Technical Hiring Manager. Generate tailored interview preparation for:\n"
                f"Candidate: {candidate.full_name if candidate else 'Applicant'}\n"
                f"Candidate Skills: {', '.join(cand_skills)}\n"
                f"Target Job: {job.title} at {job.company}\n"
                f"Role Category: {job.role_category} | Level: {job.experience_level}\n"
                f"Required Skills: {', '.join(req_skills)}\n"
                f"Job Overview: {job.description}\n\n"
                f"Provide 4 high-yield, specific questions (Technical, Project-based, Behavioral, Role-Specific) "
                f"with why it's evaluated, suggested answer framework (STAR method), and 4 checklist items.\n"
                f"Output strictly valid JSON with keys: 'questions' (list of {{category, question, why_asked, suggested_answer_framework, key_skills_evaluated}}), 'checklist' (list of strings)."
            )
            raw_res, source = llm_service.generate(prompt)
            parsed = self._parse_llm_json(raw_res)
            if parsed and "questions" in parsed:
                questions = [
                    InterviewQuestion(
                        category=q.get("category", "Technical"),
                        question=q.get("question", ""),
                        why_asked=q.get("why_asked", ""),
                        suggested_answer_framework=q.get("suggested_answer_framework", ""),
                        key_skills_evaluated=q.get("key_skills_evaluated", []),
                    )
                    for q in parsed["questions"]
                ]
                return InterviewResponse(
                    candidate_id=candidate_id,
                    job_id=job.id,
                    job_title=job.title,
                    company=job.company,
                    questions=questions,
                    preparation_checklist=parsed.get("checklist", self._default_checklist(job)),
                    source=source,
                )

        # Deterministic generation tailored to specific job skills and domain
        return self._generate_deterministic_prep(candidate, job, req_skills, pref_skills)

    def _generate_deterministic_prep(
        self, candidate, job, req_skills: List[str], pref_skills: List[str]
    ) -> InterviewResponse:
        skills_str = ", ".join(req_skills[:3]) if req_skills else "Core programming & system design"
        primary_skill = req_skills[0] if req_skills else "Python"

        questions = [
            InterviewQuestion(
                category="Technical Deep-Dive",
                question=(
                    f"How do you design, optimize, and test systems built with {skills_str}? "
                    f"Walk through your approach to error handling and performance bottlenecks."
                ),
                why_asked=f"Directly tests proficiency in the mandatory tech stack for {job.title}.",
                suggested_answer_framework=(
                    "Structure using STAR: State the architecture, specify profiling or benchmarking tools used, "
                    "and quantify latency or throughput improvements achieved."
                ),
                key_skills_evaluated=req_skills[:3],
            ),
            InterviewQuestion(
                category="Project Architecture & Tradeoffs",
                question=(
                    f"Describe an end-to-end project where you delivered a {job.role_category} feature. "
                    f"What architectural tradeoffs did you make between simplicity and scalability?"
                ),
                why_asked="Evaluates real-world software engineering maturity and decision-making.",
                suggested_answer_framework=(
                    "Explain the problem context, alternative approaches evaluated, why the chosen design was optimal, "
                    "and what you would refactor in hindsight."
                ),
                key_skills_evaluated=[primary_skill, "System Architecture"],
            ),
            InterviewQuestion(
                category="Role-Specific Problem Solving",
                question=(
                    f"At {job.company}, if a critical pipeline or service encounters unpredictable errors or high latency in production, "
                    f"what is your systematic diagnosis and triage protocol?"
                ),
                why_asked="Measures production readiness, observability practices, and calm under operational pressure.",
                suggested_answer_framework=(
                    "Detail telemetry inspection (logs, metrics, APM), isolating the failure domain, rolling back or failing over safely, "
                    "and writing a post-mortem."
                ),
                key_skills_evaluated=["Debugging", "Observability", "Reliability"],
            ),
            InterviewQuestion(
                category="Behavioral & Cross-Functional Collaboration",
                question=(
                    f"Tell me about a situation where you had a technical disagreement with a team member or stakeholder "
                    f"about how to implement a {job.role_category} requirement. How was it resolved?"
                ),
                why_asked="Evaluates constructive communication, empathy, and focus on team outcomes.",
                suggested_answer_framework=(
                    "Focus on objective data-driven decision making, respectful listening, finding consensus or testing prototypes, "
                    "and committing to the final team path."
                ),
                key_skills_evaluated=["Communication", "Collaboration", "Conflict Resolution"],
            ),
        ]

        return InterviewResponse(
            candidate_id=candidate.id if candidate else "",
            job_id=job.id,
            job_title=job.title,
            company=job.company,
            questions=questions,
            preparation_checklist=self._default_checklist(job),
            source="Curated Domain-Specific Knowledge Engine",
        )

    def _default_checklist(self, job) -> List[str]:
        req_skills = [s.skill_name for s in job.skills if s.is_required]
        skills_str = ", ".join(req_skills[:3]) if req_skills else "core competencies"
        return [
            f"Review syntax, memory models, and standard libraries for {skills_str}.",
            f"Prepare 2 concrete portfolio stories highlighting problems solved relevant to {job.title}.",
            f"Review {job.company}'s mission, technical challenges, and product offerings.",
            "Formulate 3 thoughtful questions to ask the interviewer regarding team architecture and growth expectations.",
        ]

    def _parse_llm_json(self, text: str) -> Optional[Dict[str, Any]]:
        clean = text.strip()
        first = clean.find("{")
        last = clean.rfind("}")
        if first != -1 and last != -1:
            try:
                return json.loads(clean[first:last + 1])
            except Exception:
                return None
        return None
