import json
import re
from typing import Dict, Any, List, Optional, Tuple
import httpx
from app.config import settings
from app.core.logging import logger

class LLMService:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.LLM_TIMEOUT_SECONDS

    def check_health(self) -> Dict[str, Any]:
        """Check if Ollama service is reachable and if configured model is installed."""
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=3.0)
            if response.status_code == 200:
                data = response.json()
                models = [m.get("name") for m in data.get("models", [])]
                model_present = any(self.model in m or m.startswith(self.model.split(":")[0]) for m in models)
                return {
                    "online": True,
                    "model_configured": self.model,
                    "model_available": model_present,
                    "available_models": models,
                    "status_text": f"Ollama Online (Model '{self.model}' {'Ready' if model_present else 'Not Pulled'})",
                }
        except Exception as e:
            pass

        return {
            "online": False,
            "model_configured": self.model,
            "model_available": False,
            "available_models": [],
            "status_text": "Ollama Offline (Using Deterministic Rule-Based Engine)",
        }

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
    ) -> Tuple[str, str]:
        """
        Attempts generation using local Ollama model.
        Returns: (response_text, source_engine)
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(f"{self.base_url}/api/generate", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    response_text = data.get("response", "").strip()
                    if response_text:
                        return response_text, f"Ollama ({self.model})"
        except httpx.ConnectError:
            logger.info("Ollama is not running. Switching to Deterministic Fallback Engine.")
        except Exception as e:
            logger.warning(f"Ollama generation failed: {e}. Switching to Deterministic Fallback Engine.")

        # Deterministic Fallback
        return self._deterministic_fallback_response(prompt, system_prompt), "Deterministic Fallback Engine"

    def _deterministic_fallback_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Deterministic rule-based response generator when local LLM is offline.
        Strictly indicates it is a deterministic fallback.
        """
        p_lower = prompt.lower()

        # If system requested a structured JSON tool response
        if system_prompt and "json" in system_prompt.lower() and "tool" in system_prompt.lower():
            # Check intent for tools
            if any(w in p_lower for w in ["search", "find", "look for", "jobs", "internship", "opportunities", "vacancies"]):
                # Extract role query
                role_query = "AI" if "ai" in p_lower else ("Python" if "python" in p_lower else "")
                work_mode = "Remote" if "remote" in p_lower else None
                return json.dumps({
                    "action": "call_tool",
                    "tool": "search_jobs",
                    "arguments": {
                        "query": role_query,
                        "work_mode": work_mode,
                        "limit": 5
                    }
                })
            elif any(w in p_lower for w in ["saved jobs", "my saved", "show saved"]):
                return json.dumps({
                    "action": "call_tool",
                    "tool": "get_saved_jobs",
                    "arguments": {}
                })
            elif any(w in p_lower for w in ["missing", "skill gap", "skills to learn", "what do i lack"]):
                return json.dumps({
                    "action": "call_tool",
                    "tool": "identify_skill_gaps",
                    "arguments": {}
                })
            elif any(w in p_lower for w in ["my profile", "who am i", "candidate profile"]):
                return json.dumps({
                    "action": "call_tool",
                    "tool": "get_candidate_profile",
                    "arguments": {}
                })
            elif any(w in p_lower for w in ["task", "checklist", "todo"]):
                return json.dumps({
                    "action": "call_tool",
                    "tool": "get_application_tasks",
                    "arguments": {}
                })
            elif any(w in p_lower for w in ["interview", "questions for"]):
                return json.dumps({
                    "action": "call_tool",
                    "tool": "generate_interview_questions",
                    "arguments": {}
                })
            else:
                return json.dumps({
                    "action": "final_response",
                    "message": (
                        "I am operating in deterministic offline mode because Ollama is currently offline. "
                        "You can search jobs, view recommendations, analyze skill gaps, and track applications directly."
                    )
                })

        # Plain response
        return (
            "[Deterministic Fallback Mode - Ollama Offline]\n"
            "Your request was received. To activate full natural-language synthesis, start Ollama "
            "with `ollama serve` and pull `llama3.2:3b`. In the meantime, all database search, "
            "algorithmic matching, skill gap computations, and application tracking are fully operational."
        )

llm_service = LLMService()
