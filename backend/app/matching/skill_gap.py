from typing import List, Dict, Any
from app.models.candidate import Candidate
from app.models.job import Job
from app.schemas.matching import SkillGapResponse
from app.matching.scorer import MatchingScorer

# Recommended learning roadmap references for common tech skills
LEARNING_ROADMAPS: Dict[str, Dict[str, Any]] = {
    "Docker": {
        "topics": ["Containerization Fundamentals", "Dockerfile Best Practices", "Docker Compose", "Multi-stage Builds"],
        "resource": "Official Docker Documentation & Practical Container Labs",
    },
    "Kubernetes": {
        "topics": ["Pods, Deployments, Services", "ConfigMaps & Secrets", "Ingress Controllers", "Helm Charts"],
        "resource": "Kubernetes.io Tutorials & K8s Architecture Basics",
    },
    "FastAPI": {
        "topics": ["Pydantic v2 Models", "Dependency Injection", "Asynchronous Route Handlers", "OpenAPI & Testing"],
        "resource": "FastAPI Official Documentation & Real-world REST APIs",
    },
    "PyTorch": {
        "topics": ["Tensors & Autograd", "nn.Module Design", "Dataset & DataLoader", "Transfer Learning & Fine-tuning"],
        "resource": "PyTorch 60-minute Blitz & Deep Learning with PyTorch",
    },
    "TensorFlow": {
        "topics": ["Keras Functional API", "Data Pipelines with tf.data", "Model Checkpointing", "TensorBoard Profiling"],
        "resource": "TensorFlow Official Guides",
    },
    "Large Language Models": {
        "topics": ["Prompt Engineering Strategies", "RAG Architectures", "Vector Embeddings & Vector DBs", "LangChain/LlamaIndex"],
        "resource": "DeepLearning.AI Short Courses on LLMs & Building Systems with ChatGPT/Ollama",
    },
    "SQL": {
        "topics": ["Complex Joins & Subqueries", "Window Functions", "Query Indexing & Optimization", "Schema Normalization"],
        "resource": "Mode Analytics SQL Tutorial & SQLZoo",
    },
    "Machine Learning": {
        "topics": ["Feature Engineering", "Regularization (L1/L2)", "Cross-Validation & Metrics (AUC/F1)", "Ensemble Methods (XGBoost)"],
        "resource": "Scikit-Learn User Guide & Andrew Ng's Machine Learning Specialization",
    },
    "n8n": {
        "topics": ["Workflow Automation Basics", "Webhook Triggers", "HTTP Request Nodes", "Data Transformation Expressions"],
        "resource": "n8n.io Academy & Workflow Automation Tutorials",
    },
    "AWS": {
        "topics": ["EC2, S3, IAM Roles", "Lambda Serverless", "ECS/EKS Containers", "CloudWatch Monitoring"],
        "resource": "AWS Cloud Practitioner & Solution Architect Essentials",
    },
}

class SkillGapService:
    @classmethod
    def analyze_skill_gap(cls, candidate: Candidate, job: Job) -> SkillGapResponse:
        match_result = MatchingScorer.calculate_match(candidate, job)

        missing_required = match_result.missing_required_skills
        missing_preferred = match_result.missing_preferred_skills

        recommended_topics = []
        all_missing = missing_required + missing_preferred

        for skill in all_missing:
            # Check exact or partial match in roadmaps
            for mapped_skill, info in LEARNING_ROADMAPS.items():
                if mapped_skill.lower() in skill.lower() or skill.lower() in mapped_skill.lower():
                    for t in info["topics"][:2]:
                        if t not in recommended_topics:
                            recommended_topics.append(f"{skill}: {t}")
                    break
            else:
                recommended_topics.append(f"{skill}: Core concepts and portfolio implementation")

        if not recommended_topics:
            recommended_topics = ["Candidate profile satisfies all specified skills for this role! Focus on deep domain interview preparation."]

        # Detailed guidance
        if missing_required:
            guidance = (
                f"To qualify strongly for {job.title} at {job.company}, prioritize learning the following "
                f"mandatory requirements: {', '.join(missing_required[:3])}. Building 1-2 focused projects "
                f"or completing hands-on tutorials showcasing these technologies will substantially increase "
                f"your match rate from {match_result.overall_score}% to >85%."
            )
        elif missing_preferred:
            guidance = (
                f"You satisfy all hard requirements for {job.title}! To stand out among applicants, "
                f"consider picking up preferred skills: {', '.join(missing_preferred[:3])}."
            )
        else:
            guidance = f"Exceptional match! Your skill set covers all required and preferred qualifications for {job.title}."

        return SkillGapResponse(
            candidate_id=candidate.id,
            job_id=job.id,
            job_title=job.title,
            company=job.company,
            overall_match_score=match_result.overall_score,
            missing_required_skills=missing_required,
            missing_preferred_skills=missing_preferred,
            recommended_learning_topics=recommended_topics[:6],
            detailed_guidance=guidance,
        )
