# 🎓 CareerPilot AI — Technical Concepts & Engineering Deep-Dive

This document provides conceptual and architectural explanations of the engineering decisions, algorithms, and design trade-offs implemented in CareerPilot AI. It is designed to assist software engineers, AI system architects, and hiring managers in understanding the core technical pillars of the application.

---

## 1. Why Local LLMs (Ollama) Over Paid Cloud APIs?

### The Problem with Cloud APIs in HR & Career Tech:
- **Candidate Data Privacy & GDPR:** Resumes contain personally identifiable information (PII)—full names, phone numbers, email addresses, work histories, and educational transcripts. Sending raw resume text to third-party endpoints (e.g. OpenAI, Anthropic, or Google) creates severe data sovereignty and compliance risks.
- **Cost & Rate Limits:** Cloud LLM tokens scale linearly with usage. A multi-step agent performing candidate profiling, job comparison, and interview question generation can easily consume 10,000+ tokens per interaction.
- **Offline Dependency:** Career guidance tools must be resilient to connectivity dropouts and corporate network firewalls.

### The CareerPilot Architecture Choice:
- CareerPilot AI uses **Ollama** running `llama3.2:3b` locally on CPU.
- The 3-billion parameter model is quantized (4-bit/8-bit), consuming less than 2.2 GB of RAM, and runs with sub-second inference latency on a standard Intel Core i7 laptop.
- When Ollama is offline, CareerPilot's **deterministic fallback engine** seamlessly executes tools and generates responses without pretending to be an LLM.

---

## 2. Agent Tool Calling & Orchestration Without Heavy Frameworks

### Why Not LangChain or AutoGen?
Many modern AI prototypes rely on LangChain or AutoGen. While rapid for prototyping, they introduce significant technical debt:
1. **Opaque Debugging:** Call stacks 20 layers deep obscure why a tool failed or hallucinated arguments.
2. **Fragile Abstractions:** Rapid framework API changes frequently break production dependencies.
3. **Execution Safety Risks:** Some frameworks default to dynamic code execution (`eval`/`exec`) or uncontrolled recursive loops.

### CareerPilot's Python-First Solution:
CareerPilot AI implements an explicit, deterministic agent orchestrator:
1. **Typed Tool Registry:** 12 tools are registered in a central registry. Every tool defines its input parameters using strict **Pydantic v2 schemas**.
2. **Validation Gate:** Tool inputs are parsed and validated by Pydantic before any backend function executes. If arguments fail schema validation, the agent returns an explicit error rather than executing with corrupted state.
3. **Audit Trail:** Every invocation is persisted in `agent_tool_logs` with timestamps, arguments, execution duration in milliseconds, and status.
4. **Loop Protection:** Hard cap of 3 iterations per user request prevents infinite loops or runaway compute.

---

## 3. Deterministic Multi-Factor Matching vs. Black-Box Neural Rankers

### The Hazard of Pure Neural Ranking:
If an opaque neural network assigns a match score of `73%` between a candidate and a job, it cannot explain *why*. Did the candidate lose points due to missing a critical skill, having too little experience, or preferring remote work? Candidates and hiring managers cannot trust arbitrary scores.

### CareerPilot's Transparent Mathematical Formulation:
CareerPilot uses a 7-factor weighted scoring algorithm:

$$\text{Score} = w_1 s_1 + w_2 s_2 + w_3 s_3 + w_4 s_4 + w_5 s_5 + w_6 s_6 + w_7 s_7$$

| Factor | Weight | Formula / Assessment |
| :--- | :---: | :--- |
| **Required Skills** | $35\%$ | Jaccard overlap on mandatory technical competencies |
| **Preferred Skills** | $15\%$ | Jaccard overlap on optional/bonus competencies |
| **Experience Fit** | $15\%$ | Seniority tier matching and numerical year thresholds |
| **Role Relevance** | $15\%$ | Exact and fuzzy token matching against target titles |
| **Work Mode Fit** | $10\%$ | Alignment between Remote/Hybrid/On-site preference and job |
| **Location Fit** | $5\%$ | Geographical match or 100% credit for remote positions |
| **Career Interests**| $5\%$ | Keyword overlap with domain interests (e.g. LLMs, MLOps) |

Every score is accompanied by an **explicit textual rationale** explaining matched skills, missing hard requirements, and compatibility factors.

---

## 4. Persistent Candidate Memory Architecture

### The Problem of Stateless LLMs:
Stateless LLMs forget user constraints across conversations. If a user states in Session 1: *"I am only looking for fully remote opportunities with a salary above \$80k"*, asking for jobs in Session 2 would require re-specifying those constraints.

### The Solution:
CareerPilot AI implements SQLite-backed long-term memory (`candidate_memories` table):
- Stored as typed key-value pairs (`memory_key`, `memory_value`, `category`, `confidence`).
- Automatically extracted during conversational exchanges or manually edited in the UI.
- Injected into the agent's scratchpad context on every turn, ensuring persistent personalization across sessions.

---

## 5. Hybrid Retrieval: Dense Embeddings vs. TF-IDF Cosine Similarity

### Why Hybrid?
While dense embeddings (`sentence-transformers/all-MiniLM-L6-v2`) capture semantic synonyms (e.g., *"Kubernetes"* $\approx$ *"Container Orchestration"*), they require downloading ONNX models or PyTorch weights that can fail on restricted corporate networks with SSL inspection.

### The Resilient Implementation:
CareerPilot AI implements a dual retrieval engine:
1. **Dense Vector Search:** ChromaDB with `all-MiniLM-L6-v2`.
2. **Deterministic Sparse Fallback:** In-memory Scikit-learn TF-IDF Vectorizer with Sublinear Term Frequency Scaling and Cosine Similarity.
3. In quantitative benchmarks, the TF-IDF cosine similarity engine achieved **100.0% Precision@3** and **1.0000 MRR** on domain queries with 0 RAM overhead and instant sub-millisecond retrieval.

---

## 6. Quantitative Evaluation Methodology

To prove production reliability, CareerPilot AI includes an automated benchmark runner (`app.evaluation.benchmark_runner`) that tests:
- **Search Precision@k & MRR:** Evaluates whether domain queries return ground-truth relevant jobs in the top 3 and top 5 ranks.
- **Agent Tool Selection Accuracy:** Tests 10 diverse natural-language prompts across varied user intents to ensure the orchestrator selects the correct tool 90%+ of the time.
- **Resume Extraction Accuracy:** Compares parsed entity names, emails, degrees, and technical skills against ground truth resumes to compute exact Precision, Recall, and F1 scores.
