import json
import re
import time
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.config import settings
from app.core.logging import logger
from app.services.llm_service import llm_service
from app.tools.registry import ToolRegistry, TOOL_DEFINITIONS
from app.tools.implementations import ToolExecutor
from app.agents.prompt_templates import build_system_prompt
from app.agents.intent_detector import IntentDetector
from app.repositories.candidate_repo import CandidateRepository
from app.repositories.memory_repo import MemoryRepository
from app.schemas.memory import MemoryCreate, ChatMessageCreate
from app.schemas.agent import ChatResponse, ToolExecutionStep

class AgentOrchestrator:
    def __init__(self, db: Session, candidate_id: str, conversation_id: Optional[str] = None):
        self.db = db
        self.candidate_id = candidate_id
        self.cand_repo = CandidateRepository(db)
        self.mem_repo = MemoryRepository(db)
        self.conv = self.mem_repo.get_or_create_conversation(candidate_id, conversation_id)
        self.executor = ToolExecutor(db, candidate_id=candidate_id, conversation_id=self.conv.id)
        self.max_steps = settings.MAX_AGENT_TOOL_STEPS

    def _get_candidate_context(self) -> Dict[str, Any]:
        candidate = self.cand_repo.get_by_id(self.candidate_id)
        if not candidate:
            return {"full_name": "Candidate", "profile_completeness": 0.0}

        memories = self.mem_repo.get_all_context(self.candidate_id)
        return {
            "full_name": candidate.full_name,
            "email": candidate.email,
            "profile_completeness": candidate.profile_completeness,
            "preferred_roles": json.loads(candidate.preferred_roles or "[]"),
            "preferred_work_mode": candidate.preferred_work_mode,
            "skills": [s.skill_name for s in candidate.skills],
            "memories": memories,
        }

    def process_message(self, user_message: str) -> ChatResponse:
        start_time = time.time()
        
        # 1. Save user message to database
        self.mem_repo.add_message(
            self.conv.id,
            ChatMessageCreate(sender="user", content=user_message)
        )

        # 2. Extract and store any explicit candidate preferences into persistent memory
        extracted_memories = IntentDetector.extract_memories(user_message)
        for mem in extracted_memories:
            try:
                self.mem_repo.add_memory(
                    self.candidate_id,
                    MemoryCreate(
                        category=mem["category"],
                        memory_key=mem["key"],
                        memory_value=mem["value"],
                        confidence=0.95,
                        source="conversation"
                    )
                )
            except Exception as e:
                logger.warning(f"Error saving candidate memory: {e}")

        # 3. Retrieve context and history
        candidate_info = self._get_candidate_context()
        system_prompt = build_system_prompt(candidate_info, TOOL_DEFINITIONS)
        history = self.mem_repo.get_conversation_history(self.conv.id, limit=6)
        
        history_formatted = "\n".join([f"{m.sender.upper()}: {m.content}" for m in history[:-1]])
        current_prompt = f"CONVERSATION HISTORY:\n{history_formatted}\n\nUSER: {user_message}\nASSISTANT:"

        # 4. Check LLM availability
        health = llm_service.check_health()
        llm_online = health.get("online", False) and health.get("model_available", False)

        tools_called: List[ToolExecutionStep] = []
        final_answer = ""
        source_engine = f"Ollama ({settings.OLLAMA_MODEL})" if llm_online else "Deterministic Fallback Engine"

        # 5. Agent Execution Loop
        if llm_online:
            step = 0
            scratchpad = ""
            while step < self.max_steps:
                step += 1
                prompt_with_scratchpad = current_prompt + scratchpad
                raw_response, engine = llm_service.generate(prompt_with_scratchpad, system_prompt=system_prompt)
                source_engine = engine

                # Parse JSON action
                parsed_action = self._parse_json_response(raw_response)
                if not parsed_action:
                    # Model didn't respond in JSON; retry once or treat as final text
                    final_answer = raw_response
                    break

                action_type = parsed_action.get("action")
                if action_type == "call_tool":
                    tool_name = parsed_action.get("tool")
                    tool_args = parsed_action.get("arguments", {})

                    # Inject candidate_id into tool_args if missing
                    if "candidate_id" not in tool_args:
                        tool_args["candidate_id"] = self.candidate_id

                    t_start = time.time()
                    tool_result = ToolRegistry.execute_tool(self.executor, tool_name, tool_args)
                    t_dur = (time.time() - t_start) * 1000

                    tool_step = ToolExecutionStep(
                        tool=tool_name,
                        arguments=tool_args,
                        status="SUCCESS" if tool_result.get("success", False) else "FAILED",
                        result=tool_result,
                        duration_ms=round(t_dur, 2),
                        error=tool_result.get("error")
                    )
                    tools_called.append(tool_step)

                    # Save tool execution to conversation message
                    self.mem_repo.add_message(
                        self.conv.id,
                        ChatMessageCreate(
                            sender="tool",
                            content=f"Executed {tool_name}",
                            tool_name=tool_name,
                            tool_arguments=json.dumps(tool_args),
                            tool_result=json.dumps(tool_result),
                        )
                    )

                    # Append observation to scratchpad for the next step in the loop
                    scratchpad += (
                        f"\nTOOL_CALL: {tool_name}({json.dumps(tool_args)})\n"
                        f"OBSERVATION: {json.dumps(tool_result)}\n"
                        "ASSISTANT:"
                    )
                    continue

                elif action_type == "final_response":
                    final_answer = parsed_action.get("message", "")
                    break
                else:
                    final_answer = raw_response
                    break

            if not final_answer:
                # If tool calls occurred but no final answer was generated, summarize observations
                final_answer = self._generate_fallback_summary(user_message, tools_called)

        else:
            # Deterministic Fallback Mode when Ollama is offline
            tool_tuple = IntentDetector.detect_fallback_tool(user_message)
            if tool_tuple:
                tool_name, tool_args = tool_tuple
                tool_args["candidate_id"] = self.candidate_id
                t_start = time.time()
                tool_result = ToolRegistry.execute_tool(self.executor, tool_name, tool_args)
                t_dur = (time.time() - t_start) * 1000

                tool_step = ToolExecutionStep(
                    tool=tool_name,
                    arguments=tool_args,
                    status="SUCCESS" if tool_result.get("success", False) else "FAILED",
                    result=tool_result,
                    duration_ms=round(t_dur, 2),
                    error=tool_result.get("error")
                )
                tools_called.append(tool_step)

                final_answer = self._generate_deterministic_summary(tool_name, tool_result, user_message)
            else:
                final_answer = (
                    "**CareerPilot AI** *(Operating in Deterministic Fallback Mode - Ollama Offline)*\n\n"
                    "I received your inquiry. While local Ollama inference is offline, you can directly run "
                    "all core functions:\n"
                    "- Ask me to **'Search AI Engineer jobs'** or **'Find remote Python internships'**\n"
                    "- Ask me to **'Show my saved jobs'** or **'Check my skill gaps'**\n"
                    "- Ask me to **'Prepare interview questions'**\n"
                    "- Use the left navigation tabs to inspect detailed job comparisons, recommendation matrices, and application status."
                )

        # 6. Save final assistant message to database
        self.mem_repo.add_message(
            self.conv.id,
            ChatMessageCreate(
                sender="assistant",
                content=final_answer,
            )
        )

        return ChatResponse(
            conversation_id=self.conv.id,
            message=final_answer,
            tools_called=tools_called,
            llm_source=source_engine,
            memory_extracted=extracted_memories if extracted_memories else None,
        )

    def _parse_json_response(self, text: str) -> Optional[Dict[str, Any]]:
        """Safely parse JSON response from LLM output, extracting from code blocks if present."""
        clean = text.strip()
        # Look for markdown json codeblock
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', clean, re.DOTALL)
        if match:
            clean = match.group(1).strip()
        elif clean.startswith("{") and clean.endswith("}"):
            pass
        else:
            # Try to find first { and last }
            first_brace = clean.find("{")
            last_brace = clean.rfind("}")
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                clean = clean[first_brace:last_brace + 1]

        try:
            return json.loads(clean)
        except Exception:
            return None

    def _generate_fallback_summary(self, user_query: str, tools_called: List[ToolExecutionStep]) -> str:
        if not tools_called:
            return "I processed your request, but no specific action was required."

        last_tool = tools_called[-1]
        return self._generate_deterministic_summary(last_tool.tool, last_tool.result, user_query)

    def _generate_deterministic_summary(self, tool_name: str, tool_result: Dict[str, Any], query: str) -> str:
        if not tool_result.get("success", False):
            return f"**Action Attempted:** `{tool_name}`\n\n**Notice:** {tool_result.get('error', 'Execution error encountered.')}"

        if tool_name == "search_jobs":
            jobs = tool_result.get("jobs", [])
            total = tool_result.get("total_found", len(jobs))
            lines = [
                f"### Job Search Results ({total} opportunities found)\n",
                f"Here are the top matches from our local catalogue:\n"
            ]
            for idx, j in enumerate(jobs[:5], 1):
                match_badge = f"**Match Score: {j.get('match_score', 'N/A')}%**" if "match_score" in j else ""
                lines.append(
                    f"{idx}. **{j['title']}** at **{j['company']}**\n"
                    f"   - **Location:** {j['location']} ({j['work_mode']}) | **Level:** {j['experience_level']}\n"
                    f"   - **Salary:** {j.get('salary', 'Competitive')} | {match_badge}\n"
                    f"   - **Key Skills:** {', '.join(j.get('skills', [])[:5])}\n"
                    f"   - *[Job ID: `{j['id']}`]*\n"
                )
            lines.append("\n*Tip: To evaluate alignment, ask 'Compare job with ID <job_id>' or 'What skills am I missing for this job?'*")
            return "\n".join(lines)

        elif tool_name == "get_saved_jobs":
            saved = tool_result.get("saved_jobs", [])
            if not saved:
                return "You do not have any saved job opportunities yet. Search for jobs and ask me to 'Save this opportunity' to track them!"
            lines = [f"### Saved Opportunities ({len(saved)})\n"]
            for idx, s in enumerate(saved, 1):
                lines.append(f"{idx}. **{s['title']}** at **{s['company']}** ({s['work_mode']}, {s['location']}) - *Saved on {s['saved_at'][:10]}*")
            return "\n".join(lines)

        elif tool_name == "identify_skill_gaps":
            lines = [
                f"### Skill Gap Analysis: {tool_result.get('job_title')} at {tool_result.get('company')}\n",
                f"- **Overall Match Score:** `{tool_result.get('overall_match_score')}%`",
                f"- **Missing Required Skills:** {', '.join(tool_result.get('missing_required_skills', [])) or 'None! You meet all hard requirements.'}",
                f"- **Missing Preferred Skills:** {', '.join(tool_result.get('missing_preferred_skills', [])) or 'None'}\n",
                f"**Actionable Learning Roadmap:**"
            ]
            for topic in tool_result.get("recommended_learning_topics", []):
                lines.append(f"- {topic}")
            lines.append(f"\n**Strategic Guidance:** {tool_result.get('detailed_guidance')}")
            return "\n".join(lines)

        elif tool_name == "generate_interview_questions":
            questions = tool_result.get("questions", [])
            checklist = tool_result.get("preparation_checklist", [])
            lines = [
                f"### Tailored Interview Preparation: {tool_result.get('job_title')} ({tool_result.get('company')})\n",
                "Here are high-yield interview questions designed around the role's competencies:\n"
            ]
            for idx, q in enumerate(questions, 1):
                lines.append(
                    f"**{idx}. [{q['category']}]** {q['question']}\n"
                    f"   - *Why Evaluated:* {q['why_asked']}\n"
                    f"   - *Suggested Framework:* {q['framework']}\n"
                )
            lines.append("### Application Preparation Checklist:")
            for item in checklist:
                lines.append(f"- [ ] {item}")
            lines.append(f"\n*{tool_result.get('disclaimer')}*")
            return "\n".join(lines)

        elif tool_name == "get_candidate_profile":
            prof = tool_result.get("profile", {})
            skills_str = ", ".join([s["name"] for s in prof.get("skills", [])])
            roles_str = ", ".join(prof.get("preferred_roles", []))
            return (
                f"### Candidate Profile: {prof.get('full_name')}\n"
                f"- **Email:** {prof.get('email')}\n"
                f"- **Education:** {prof.get('degree') or ''} {prof.get('education') or 'Not specified'}\n"
                f"- **Experience:** {prof.get('experience_years', 0)} years ({prof.get('experience_level', 'Entry-level')})\n"
                f"- **Target Roles:** {roles_str or 'General'}\n"
                f"- **Work Mode:** {prof.get('preferred_work_mode')}\n"
                f"- **Verified Skills:** {skills_str or 'No skills recorded yet'}\n"
                f"- **Profile Completeness:** `{prof.get('profile_completeness', 0)}%`"
            )

        elif tool_name == "compare_job_with_candidate":
            lines = [
                f"### Profile Alignment Comparison: {tool_result.get('job_title')} ({tool_result.get('company')})\n",
                f"- **Overall Match Score:** `{tool_result.get('overall_score')}%`",
                f"- **Matched Required Skills:** {', '.join(tool_result.get('matched_required_skills', [])) or 'None'}",
                f"- **Missing Required Skills:** {', '.join(tool_result.get('missing_required_skills', [])) or 'None'}",
                f"- **Work Mode Compatible:** {'Yes' if tool_result.get('work_mode_compatible') else 'No'}",
                f"- **Experience Compatible:** {'Yes' if tool_result.get('experience_compatible') else 'No'}\n",
                f"**Evaluation Summary:** {tool_result.get('explanation')}\n",
                f"*{tool_result.get('disclaimer')}*"
            ]
            return "\n".join(lines)

        return f"Completed tool `{tool_name}`: {tool_result.get('message', 'Success')}"
