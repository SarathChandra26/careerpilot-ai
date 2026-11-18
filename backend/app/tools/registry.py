from typing import Dict, Any, List
from app.tools.implementations import ToolExecutor

TOOL_DEFINITIONS = [
    {
        "name": "search_jobs",
        "description": "Search the job database by query string, role category, experience level, work mode, or location.",
        "parameters": {
            "query": "string (optional): Title or keyword search (e.g. 'AI Engineer', 'Python')",
            "role_category": "string (optional): e.g. 'AI Engineer', 'Backend Developer'",
            "experience_level": "string (optional): 'Internship', 'Entry-level', 'Mid-level'",
            "work_mode": "string (optional): 'Remote', 'Hybrid', 'On-site'",
            "location": "string (optional): e.g. 'Remote', 'San Francisco'",
            "limit": "integer (optional, default 5): Number of job records to return",
        }
    },
    {
        "name": "get_candidate_profile",
        "description": "Retrieve the active candidate's professional profile, skills, education, and preferences.",
        "parameters": {
            "candidate_id": "string (optional): Candidate ID. Uses active candidate if omitted."
        }
    },
    {
        "name": "update_candidate_preferences",
        "description": "Update the candidate's job preferences such as preferred roles, locations, or work mode.",
        "parameters": {
            "preferred_roles": "list of strings (optional): e.g. ['AI Engineer', 'Machine Learning Engineer']",
            "preferred_locations": "list of strings (optional): e.g. ['Remote', 'New York']",
            "preferred_work_mode": "string (optional): 'Remote', 'Hybrid', 'On-site', 'Any'",
            "career_interests": "list of strings (optional): e.g. ['RAG', 'Agentic AI']"
        }
    },
    {
        "name": "compare_job_with_candidate",
        "description": "Perform algorithmic profile comparison with a job, returning match score and skill breakdown.",
        "parameters": {
            "job_id": "string (required): The ID of the job to evaluate"
        }
    },
    {
        "name": "save_job",
        "description": "Save a job opportunity to the candidate's saved jobs list for future reference.",
        "parameters": {
            "job_id": "string (required): The ID of the job to save",
            "notes": "string (optional): Candidate notes"
        }
    },
    {
        "name": "remove_saved_job",
        "description": "Remove a job from the candidate's saved jobs list.",
        "parameters": {
            "job_id": "string (required): The ID of the job to remove"
        }
    },
    {
        "name": "get_saved_jobs",
        "description": "Retrieve all saved jobs for the candidate.",
        "parameters": {}
    },
    {
        "name": "create_application_task",
        "description": "Create an actionable preparation or application task for a job.",
        "parameters": {
            "title": "string (required): Title of task (e.g. 'Customize resume for AI role', 'Review PyTorch')",
            "job_id": "string (optional): Associated job ID",
            "description": "string (optional): Task details"
        }
    },
    {
        "name": "get_application_tasks",
        "description": "Retrieve the list of application tasks and checklist items for the candidate.",
        "parameters": {
            "is_completed": "boolean (optional): Filter completed vs pending tasks"
        }
    },
    {
        "name": "update_application_status",
        "description": "Update job application tracking status (Interested, Saved, Preparing, Applied, Interview Scheduled, Rejected, Offer Received).",
        "parameters": {
            "job_id": "string (required): Job ID",
            "status": "string (required): New application status",
            "notes": "string (optional): Status update notes"
        }
    },
    {
        "name": "generate_interview_questions",
        "description": "Generate tailored technical, project-based, and behavioral interview questions for a job.",
        "parameters": {
            "job_id": "string (optional): Job ID to tailor questions for"
        }
    },
    {
        "name": "identify_skill_gaps",
        "description": "Analyze missing required and preferred skills for a job and provide targeted learning topics.",
        "parameters": {
            "job_id": "string (optional): Job ID to analyze gaps for"
        }
    }
]

class ToolRegistry:
    @staticmethod
    def get_tool_definitions() -> List[Dict[str, Any]]:
        return TOOL_DEFINITIONS

    @staticmethod
    def execute_tool(executor: ToolExecutor, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if not hasattr(executor, tool_name):
            return {
                "success": False,
                "error": f"Tool '{tool_name}' is not registered or recognized."
            }
        method = getattr(executor, tool_name)
        return method(args)
