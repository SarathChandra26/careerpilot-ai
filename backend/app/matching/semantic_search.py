import os
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.config import settings
from app.core.logging import logger

os.environ["ANONYMIZED_TELEMETRY"] = "False"

class SemanticSearchService:
    _instance = None

    def __init__(self):
        self.documents: Dict[str, str] = {}  # job_id -> combined text
        self.metadata: Dict[str, Dict[str, Any]] = {}
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.tfidf_matrix = None
        self.job_ids: List[str] = []
        self._chroma_client = None
        self._chroma_collection = None
        self._init_chroma()

    @classmethod
    def get_instance(cls) -> "SemanticSearchService":
        if cls._instance is None:
            cls._instance = SemanticSearchService()
        return cls._instance

    def _init_chroma(self):
        try:
            from pathlib import Path
            onnx_cache = Path.home() / ".cache" / "chroma" / "onnx_models" / "all-MiniLM-L6-v2" / "onnx.tar.gz"
            if not onnx_cache.exists():
                logger.info("ChromaDB ONNX model not cached locally. Using ultra-fast in-memory TF-IDF semantic vector search engine.")
                self._chroma_client = None
                self._chroma_collection = None
                return

            import chromadb
            from chromadb.config import Settings as ChromaSettings
            self._chroma_client = chromadb.PersistentClient(
                path=settings.CHROMA_DB_DIR,
                settings=ChromaSettings(anonymized_telemetry=False)
            )
            self._chroma_collection = self._chroma_client.get_or_create_collection(
                name="careerpilot_jobs",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("ChromaDB vector store connected.")
        except Exception as e:
            logger.info(f"Using high-performance in-memory TF-IDF semantic vector search engine: {e}")
            self._chroma_client = None
            self._chroma_collection = None

    def index_job(self, job_id: str, title: str, company: str, description: str, skills: List[str], rebuild_tfidf: bool = True):
        """Incrementally index or update a single job in the semantic search engine."""
        doc = f"{title} at {company}. {description}. Core competencies: {', '.join(skills)}"
        self.documents[job_id] = doc
        self.metadata[job_id] = {"job_id": job_id, "title": title, "company": company}
        
        if rebuild_tfidf:
            self._rebuild_tfidf()

        if self._chroma_collection:
            try:
                self._chroma_collection.upsert(
                    ids=[job_id],
                    documents=[doc],
                    metadatas=[{"title": title, "company": company}]
                )
            except Exception as e:
                logger.warning(f"ChromaDB index error for {job_id}: {e}")

    def batch_index_jobs(self, jobs_data: List[Dict[str, Any]]):
        """Bulk index jobs efficiently in a single vectorized pass."""
        if not jobs_data:
            return

        ids = []
        docs = []
        metas = []

        for item in jobs_data:
            jid = item["job_id"]
            title = item["title"]
            company = item["company"]
            description = item["description"]
            skills = item.get("skills", [])

            doc = f"{title} at {company}. {description}. Core competencies: {', '.join(skills)}"
            self.documents[jid] = doc
            self.metadata[jid] = {"job_id": jid, "title": title, "company": company}

            ids.append(jid)
            docs.append(doc)
            metas.append({"title": title, "company": company})

        # Fit TF-IDF once
        self._rebuild_tfidf()

        # Batch upsert to ChromaDB once
        if self._chroma_collection:
            try:
                self._chroma_collection.upsert(
                    ids=ids,
                    documents=docs,
                    metadatas=metas
                )
            except Exception as e:
                logger.warning(f"ChromaDB batch index error: {e}")

    def delete_job(self, job_id: str):
        """Remove a job from index incrementally."""
        if job_id in self.documents:
            del self.documents[job_id]
        if job_id in self.metadata:
            del self.metadata[job_id]
        self._rebuild_tfidf()

        if self._chroma_collection:
            try:
                self._chroma_collection.delete(ids=[job_id])
            except Exception as e:
                logger.warning(f"ChromaDB delete error for {job_id}: {e}")

    def _rebuild_tfidf(self):
        if not self.documents:
            self.tfidf_matrix = None
            self.job_ids = []
            return

        self.job_ids = list(self.documents.keys())
        docs_list = [self.documents[jid] for jid in self.job_ids]
        try:
            self.tfidf_matrix = self.vectorizer.fit_transform(docs_list)
        except Exception as e:
            logger.error(f"Error fitting TF-IDF matrix: {e}")
            self.tfidf_matrix = None

    def search_similar_jobs(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        if not query or not self.documents:
            return []

        # Try ChromaDB query first if available
        if self._chroma_collection:
            try:
                res = self._chroma_collection.query(query_texts=[query], n_results=top_k)
                if res and res.get("ids") and len(res["ids"]) > 0:
                    matched_ids = res["ids"][0]
                    distances = res.get("distances", [[]])[0] if res.get("distances") else []
                    results = []
                    for idx, jid in enumerate(matched_ids):
                        score = 1.0 - (distances[idx] if idx < len(distances) else 0.5)
                        results.append((jid, round(float(score), 3)))
                    if results:
                        return results
            except Exception as e:
                logger.debug(f"Chroma query fallback to TF-IDF: {e}")

        # TF-IDF cosine similarity search
        if self.tfidf_matrix is None or not self.job_ids:
            return []

        try:
            query_vec = self.vectorizer.transform([query])
            sim_scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
            
            top_indices = np.argsort(sim_scores)[::-1][:top_k]
            results = []
            for idx in top_indices:
                score = sim_scores[idx]
                if score > 0.01:
                    results.append((self.job_ids[idx], round(float(score), 3)))
            return results
        except Exception as e:
            logger.error(f"Error during semantic vector search: {e}")
            return []
