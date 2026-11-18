import json
import time
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.agent_log import AgentToolLog
from app.repositories.candidate_repo import CandidateRepository
from app.repositories.job_repo import JobRepository
from app.repositories.application_repo import ApplicationRepository
from app.repositories.memory_repo import MemoryRepository
from app.matching.scorer import MatchingScorer
from app.matching.skill_gap import SkillGapService
from app.schemas.job import JobFilterParams
from app.schemas.candidate import CandidateUpdate
from app.schemas.application import ApplicationCreate, TaskCreate
from app.tools.schemas import (
    SearchJobsArgs,
    GetCandidateProfileArgs,
    UpdateCandidatePreferencesArgs,
    CompareJobWithCandidateArgs,
    SaveJobArgs,
    RemoveSavedJobArgs,
    GetSavedJobsArgs,
    CreateApplicationTaskArgs,
    GetApplicationTasksArgs,
    UpdateApplicationStatusArgs,
    GenerateInterviewQuestionsArgs,
    IdentifySkillGapsArgs,
)

class ToolExecutor:
    def __init__(self, db: Session, candidate_id: Optional[str] = None, conversation_id: Optional[str] = None):
        self.db = db
        self.candidate_id = candidate_id
        self.conversation_id = conversation_id
        self.cand_repo = CandidateRepository(db)
        self.job_repo = JobRepository(db)
        self.app_repo = ApplicationRepository(db)
        self.mem_repo = MemoryRepository(db)

    def _resolve_candidate_id(self, provided_id: Optional[str]) -> Optional[str]:
        if provided_id and provided_id.strip():
            return provided_id.strip()
        if self.candidate_id:
            return self.candidate_id
        first = self.cand_repo.get_first_or_default()
        return first.id if first else None

    def _log_execution(self, tool_name: str, args: Dict[str, Any], status: str, duration_ms: float, error: Optional[str] = None, summary: Optional[str] = None):
        try:
            log_entry = AgentToolLog(
                candidate_id=self.candidate_id,
                conversation_id=self.conversation_id,
                tool_name=tool_name,
                arguments=json.dumps(args),
                execution_status=status,
                execution_duration_ms=round(duration_ms, 2),
                error_message=error,
                result_summary=summary[:500] if summary else None,
            )
            self.db.add(log_entry)
            self.db.commit()
        except Exception:
            pass

    # Tool 1: search_jobs
    def search_jobs(self, raw_args: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        try:
            args = SearchJobsArgs(**raw_args)
            params = JobFilterParams(
                query=args.query,
                role_category=args.role_category,
                experience_level=args.experience_level,
                work_mode=args.work_mode,
                location=args.location,
                min_salary=args.min_salary,
                limit=args.limit,
                offset=0,
            )
            jobs, total = self.job_repo.search_and_filter(params)
            
            # Format results
            results = []
            candidate_id = self._resolve_candidate_id(None)
            candidate = self.cand_repo.get_by_id(candidate_id) if candidate_id else None

            for j in jobs:
                item = {
                    "id": j.id,
                    "title": j.title,
                    "company": j.company,
                    "role_category": j.role_category,
                    "experience_level": j.experience_level,
                    "location": j.location,
                    "work_mode": j.work_mode,
                    "salary": f"${j.salary_min:,} - ${j.salary_max:,}" if j.salary_min and j.salary_max else "Competitive",
                    "skills": [s.skill_name for s in j.skills],
                    "is_synthetic_demonstration": j.is_synthetic,
                }
                if candidate:
                    match = MatchingScorer.calculate_match(candidate, j)
                    item["match_score"] = match.overall_score
                    item["matched_skills"] = match.matched_required_skills
                    item["missing_required_skills"] = match.missing_required_skills
                results.append(item)

            # Sort by match score if candidate profile available
            if candidate:
                results.sort(key=lambda x: x.get("match_score", 0), reverse=True)

            dur = (time.time() - start) * 1000
            self._log_execution("search_jobs", raw_args, "SUCCESS", dur, summary=f"Found {len(results)} jobs")
            return {
                "success": True,
                "total_found": total,
                "returned_count": len(results),
                "jobs": results,
            }
        except Exception as e:
            dur = (time.time() - start) * 1000
            self._log_execution("search_jobs", raw_args, "FAILED", dur, error=str(e))
            return {"success": False, "error": str(e)}

    # Tool 2: get_candidate_profile
    def get_candidate_profile(self, raw_args: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        try:
            args = GetCandidateProfileArgs(**raw_args)
            cid = self._resolve_candidate_id(args.candidate_id)
            if not cid:
                return {"success": False, "error": "No candidate profile found. Please create a profile first."}

            candidate = self.cand_repo.get_by_id(cid)
            if not candidate:
                return {"success": False, "error": f"Candidate with id {cid} not found"}

            profile_data = {
                "id": candidate.id,
                "full_name": candidate.full_name,
                "email": candidate.email,
                "education": candidate.education,
                "degree": candidate.degree,
                "experience_years": candidate.experience_years,
                "experience_level": candidate.experience_level,
                "preferred_roles": json.loads(candidate.preferred_roles or "[]"),
                "preferred_locations": json.loads(candidate.preferred_locations or "[]"),
                "preferred_work_mode": candidate.preferred_work_mode,
                "career_interests": json.loads(candidate.career_interests or "[]"),
                "skills": [
                    {"name": s.skill_name, "category": s.category, "proficiency": s.proficiency}
                    for s in candidate.skills
                ],
                "profile_completeness": candidate.profile_completeness,
            }
            dur = (time.time() - start) * 1000
            self._log_execution("get_candidate_profile", raw_args, "SUCCESS", dur, summary=f"Profile for {candidate.full_name}")
            return {"success": True, "profile": profile_data}
        except Exception as e:
            dur = (time.time() - start) * 1000
            self._log_execution("get_candidate_profile", raw_args, "FAILED", dur, error=str(e))
            return {"success": False, "error": str(e)}

    # Tool 3: update_candidate_preferences
    def update_candidate_preferences(self, raw_args: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        try:
            args = UpdateCandidatePreferencesArgs(**raw_args)
            cid = self._resolve_candidate_id(args.candidate_id)
            if not cid:
                return {"success": False, "error": "Candidate ID required to update preferences"}

            update_data = {}
            if args.preferred_roles is not None:
                update_data["preferred_roles"] = args.preferred_roles
            if args.preferred_locations is not None:
                update_data["preferred_locations"] = args.preferred_locations
            if args.preferred_work_mode is not None:
                update_data["preferred_work_mode"] = args.preferred_work_mode
            if args.salary_expectation_min is not None:
                update_data["salary_expectation_min"] = args.salary_expectation_min
            if args.career_interests is not None:
                update_data["career_interests"] = args.career_interests

            cand_update = CandidateUpdate(**update_data)
            updated = self.cand_repo.update(cid, cand_update)
            if not updated:
                return {"success": False, "error": "Candidate not found"}

            dur = (time.time() - start) * 1000
            self._log_execution("update_candidate_preferences", raw_args, "SUCCESS", dur, summary="Updated preferences")
            return {
                "success": True,
                "message": "Preferences updated successfully",
                "preferred_roles": json.loads(updated.preferred_roles or "[]"),
                "preferred_work_mode": updated.preferred_work_mode,
                "preferred_locations": json.loads(updated.preferred_locations or "[]"),
            }
        except Exception as e:
            dur = (time.time() - start) * 1000
            self._log_execution("update_candidate_preferences", raw_args, "FAILED", dur, error=str(e))
            return {"success": False, "error": str(e)}

    # Tool 4: compare_job_with_candidate
    def compare_job_with_candidate(self, raw_args: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        try:
            args = CompareJobWithCandidateArgs(**raw_args)
            cid = self._resolve_candidate_id(args.candidate_id)
            candidate = self.cand_repo.get_by_id(cid) if cid else None
            job = self.job_repo.get_by_id(args.job_id)

            if not job:
                return {"success": False, "error": f"Job with ID '{args.job_id}' not found"}
            if not candidate:
                return {"success": False, "error": "Active candidate profile not found"}

            match = MatchingScorer.calculate_match(candidate, job)
            dur = (time.time() - start) * 1000
            self._log_execution("compare_job_with_candidate", raw_args, "SUCCESS", dur, summary=f"Match: {match.overall_score}%")
            return {
                "success": True,
                "job_title": job.title,
                "company": job.company,
                "overall_score": match.overall_score,
                "matched_required_skills": match.matched_required_skills,
                "missing_required_skills": match.missing_required_skills,
                "matched_preferred_skills": match.matched_preferred_skills,
                "missing_preferred_skills": match.missing_preferred_skills,
                "experience_compatible": match.experience_compatible,
                "work_mode_compatible": match.work_mode_compatible,
                "location_compatible": match.location_compatible,
                "explanation": match.explanation,
                "disclaimer": match.disclaimer,
            }
        except Exception as e:
            dur = (time.time() - start) * 1000
            self._log_execution("compare_job_with_candidate", raw_args, "FAILED", dur, error=str(e))
            return {"success": False, "error": str(e)}

    # Tool 5: save_job
    def save_job(self, raw_args: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        try:
            args = SaveJobArgs(**raw_args)
            cid = self._resolve_candidate_id(args.candidate_id)
            if not cid:
                return {"success": False, "error": "Candidate ID required to save job"}

            job = self.job_repo.get_by_id(args.job_id)
            if not job:
                return {"success": False, "error": f"Job with ID '{args.job_id}' not found"}

            saved = self.job_repo.save_job(cid, args.job_id, notes=args.notes)
            dur = (time.time() - start) * 1000
            self._log_execution("save_job", raw_args, "SUCCESS", dur, summary=f"Saved job {job.title}")
            return {
                "success": True,
                "message": f"Saved '{job.title}' at {job.company} to your saved opportunities.",
                "job_id": job.id,
            }
        except Exception as e:
            dur = (time.time() - start) * 1000
            self._log_execution("save_job", raw_args, "FAILED", dur, error=str(e))
            return {"success": False, "error": str(e)}

    # Tool 6: remove_saved_job
    def remove_saved_job(self, raw_args: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        try:
            args = RemoveSavedJobArgs(**raw_args)
            cid = self._resolve_candidate_id(args.candidate_id)
            if not cid:
                return {"success": False, "error": "Candidate ID required"}

            removed = self.job_repo.remove_saved_job(cid, args.job_id)
            dur = (time.time() - start) * 1000
            self._log_execution("remove_saved_job", raw_args, "SUCCESS" if removed else "FAILED", dur)
            if removed:
                return {"success": True, "message": "Job removed from your saved list."}
            else:
                return {"success": False, "error": "Job was not in your saved list."}
        except Exception as e:
            dur = (time.time() - start) * 1000
            self._log_execution("remove_saved_job", raw_args, "FAILED", dur, error=str(e))
            return {"success": False, "error": str(e)}

    # Tool 7: get_saved_jobs
    def get_saved_jobs(self, raw_args: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        try:
            args = GetSavedJobsArgs(**raw_args)
            cid = self._resolve_candidate_id(args.candidate_id)
            if not cid:
                return {"success": False, "error": "Candidate ID required"}

            saved_items = self.job_repo.get_saved_jobs(cid)
            jobs_list = []
            for item in saved_items:
                j = item.job
                jobs_list.append({
                    "job_id": j.id,
                    "title": j.title,
                    "company": j.company,
                    "location": j.location,
                    "work_mode": j.work_mode,
                    "saved_at": item.saved_at.isoformat(),
                    "notes": item.notes,
                })

            dur = (time.time() - start) * 1000
            self._log_execution("get_saved_jobs", raw_args, "SUCCESS", dur, summary=f"Found {len(jobs_list)} saved jobs")
            return {
                "success": True,
                "total_saved": len(jobs_list),
                "saved_jobs": jobs_list,
            }
        except Exception as e:
            dur = (time.time() - start) * 1000
            self._log_execution("get_saved_jobs", raw_args, "FAILED", dur, error=str(e))
            return {"success": False, "error": str(e)}

    # Tool 8: create_application_task
    def create_application_task(self, raw_args: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        try:
            args = CreateApplicationTaskArgs(**raw_args)
            cid = self._resolve_candidate_id(args.candidate_id)
            if not cid:
                return {"success": False, "error": "Candidate ID required"}

            task_in = TaskCreate(
                title=args.title,
                description=args.description,
                job_id=args.job_id,
            )
            task = self.app_repo.create_task(cid, task_in)
            dur = (time.time() - start) * 1000
            self._log_execution("create_application_task", raw_args, "SUCCESS", dur, summary=f"Task: {task.title}")
            return {
                "success": True,
                "task_id": task.id,
                "title": task.title,
                "message": f"Created task: '{task.title}'",
            }
        except Exception as e:
            dur = (time.time() - start) * 1000
            self._log_execution("create_application_task", raw_args, "FAILED", dur, error=str(e))
            return {"success": False, "error": str(e)}

    # Tool 9: get_application_tasks
    def get_application_tasks(self, raw_args: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        try:
            args = GetApplicationTasksArgs(**raw_args)
            cid = self._resolve_candidate_id(args.candidate_id)
            if not cid:
                return {"success": False, "error": "Candidate ID required"}

            tasks = self.app_repo.get_tasks_by_candidate(cid, is_completed=args.is_completed)
            task_list = [
                {
                    "id": t.id,
                    "title": t.title,
                    "description": t.description,
                    "is_completed": t.is_completed,
                    "job_id": t.job_id,
                    "created_at": t.created_at.isoformat(),
                }
                for t in tasks
            ]
            dur = (time.time() - start) * 1000
            self._log_execution("get_application_tasks", raw_args, "SUCCESS", dur, summary=f"{len(task_list)} tasks")
            return {
                "success": True,
                "total_tasks": len(task_list),
                "tasks": task_list,
            }
        except Exception as e:
            dur = (time.time() - start) * 1000
            self._log_execution("get_application_tasks", raw_args, "FAILED", dur, error=str(e))
            return {"success": False, "error": str(e)}

    # Tool 10: update_application_status
    def update_application_status(self, raw_args: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        try:
            args = UpdateApplicationStatusArgs(**raw_args)
            cid = self._resolve_candidate_id(args.candidate_id)
            if not cid:
                return {"success": False, "error": "Candidate ID required"}

            job = self.job_repo.get_by_id(args.job_id)
            if not job:
                return {"success": False, "error": f"Job with ID '{args.job_id}' not found"}

            app_in = ApplicationCreate(job_id=args.job_id, status=args.status, notes=args.notes)
            application = self.app_repo.create(cid, app_in)

            dur = (time.time() - start) * 1000
            self._log_execution("update_application_status", raw_args, "SUCCESS", dur, summary=f"Status: {args.status}")
            return {
                "success": True,
                "message": f"Updated application status for '{job.title}' to '{args.status}'.",
                "application_id": application.id,
                "status": application.status,
            }
        except Exception as e:
            dur = (time.time() - start) * 1000
            self._log_execution("update_application_status", raw_args, "FAILED", dur, error=str(e))
            return {"success": False, "error": str(e)}

    # Tool 11: generate_interview_questions
    def generate_interview_questions(self, raw_args: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        try:
            args = GenerateInterviewQuestionsArgs(**raw_args)
            cid = self._resolve_candidate_id(args.candidate_id)
            candidate = self.cand_repo.get_by_id(cid) if cid else None

            # Resolve job
            job = None
            if args.job_id:
                job = self.job_repo.get_by_id(args.job_id)
            elif candidate:
                # Use latest saved job or top recommendation
                saved = self.job_repo.get_saved_jobs(cid)
                if saved:
                    job = saved[0].job
                else:
                    jobs, _ = self.job_repo.search_and_filter(JobFilterParams(limit=1))
                    job = jobs[0] if jobs else None

            if not job:
                return {"success": False, "error": "No job found to generate interview questions for."}

            # Generate tailored questions based on job description & required skills
            req_skills = [s.skill_name for s in job.skills if s.is_required]
            skills_str = ", ".join(req_skills[:4]) if req_skills else "Python, Machine Learning"

            questions = [
                {
                    "category": "Technical",
                    "question": f"Can you explain your experience with {skills_str} and walk through how you apply them in production?",
                    "why_asked": f"Evaluates core technical competency required for {job.title}.",
                    "framework": "STAR method (Situation, Task, Action, Result). Highlight specific architectural decisions and tradeoffs.",
                },
                {
                    "category": "Project-based",
                    "question": f"Describe a notable project where you implemented {req_skills[0] if req_skills else 'data processing'}. What engineering hurdles did you overcome?",
                    "why_asked": "Assesses end-to-end practical delivery capabilities.",
                    "framework": "Detail problem scope, tools chosen, failure modes encountered, and measurable impact.",
                },
                {
                    "category": "Role-Specific Problem Solving",
                    "question": f"At {job.company}, how would you approach debugging a high-latency bottleneck in a {job.role_category} workflow?",
                    "why_asked": "Tests systematic reasoning and observability mindset.",
                    "framework": "Outline hypothesis testing, profiling techniques, logging, and incremental resolution.",
                },
                {
                    "category": "Behavioral",
                    "question": "Tell me about a time you had to quickly adapt to an unfamiliar framework or tool under a tight project deadline.",
                    "why_asked": "Measures learning agility, adaptability, and resilience.",
                    "framework": "Explain your rapid learning protocol, how you prioritized essential concepts, and delivered on time.",
                }
            ]

            checklist = [
                f"Review core documentation and best practices for: {skills_str}.",
                f"Prepare 2 concrete portfolio stories highlighting projects aligned with {job.title}.",
                f"Study {job.company}'s product architecture and recent engineering blog posts.",
                "Conduct a mock 30-minute technical interview covering data structures and system design."
            ]

            dur = (time.time() - start) * 1000
            self._log_execution("generate_interview_questions", raw_args, "SUCCESS", dur, summary=f"Generated {len(questions)} questions")
            return {
                "success": True,
                "job_title": job.title,
                "company": job.company,
                "questions": questions,
                "preparation_checklist": checklist,
                "disclaimer": "These questions are AI-suggested preparation prompts based on role requirements.",
            }
        except Exception as e:
            dur = (time.time() - start) * 1000
            self._log_execution("generate_interview_questions", raw_args, "FAILED", dur, error=str(e))
            return {"success": False, "error": str(e)}

    # Tool 12: identify_skill_gaps
    def identify_skill_gaps(self, raw_args: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        try:
            args = IdentifySkillGapsArgs(**raw_args)
            cid = self._resolve_candidate_id(args.candidate_id)
            candidate = self.cand_repo.get_by_id(cid) if cid else None
            if not candidate:
                return {"success": False, "error": "Candidate profile not found"}

            job = None
            if args.job_id:
                job = self.job_repo.get_by_id(args.job_id)
            else:
                saved = self.job_repo.get_saved_jobs(cid)
                if saved:
                    job = saved[0].job
                else:
                    jobs, _ = self.job_repo.search_and_filter(JobFilterParams(limit=1))
                    job = jobs[0] if jobs else None

            if not job:
                return {"success": False, "error": "No job available for skill gap inspection."}

            gap_result = SkillGapService.analyze_skill_gap(candidate, job)
            dur = (time.time() - start) * 1000
            self._log_execution("identify_skill_gaps", raw_args, "SUCCESS", dur, summary=f"Gap analysis for {job.title}")
            return {
                "success": True,
                "job_title": job.title,
                "company": job.company,
                "overall_match_score": gap_result.overall_match_score,
                "missing_required_skills": gap_result.missing_required_skills,
                "missing_preferred_skills": gap_result.missing_preferred_skills,
                "recommended_learning_topics": gap_result.recommended_learning_topics,
                "detailed_guidance": gap_result.detailed_guidance,
            }
        except Exception as e:
            dur = (time.time() - start) * 1000
            self._log_execution("identify_skill_gaps", raw_args, "FAILED", dur, error=str(e))
            return {"success": False, "error": str(e)}
