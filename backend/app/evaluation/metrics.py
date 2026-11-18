from typing import List, Set, Dict, Any

def precision_at_k(retrieved_ids: List[str], ground_truth_ids: Set[str], k: int = 5) -> float:
    if k <= 0 or not retrieved_ids:
        return 0.0
    top_k = retrieved_ids[:k]
    relevant_retrieved = sum(1 for item in top_k if item in ground_truth_ids)
    return round(relevant_retrieved / min(k, len(top_k)), 4)

def recall_at_k(retrieved_ids: List[str], ground_truth_ids: Set[str], k: int = 5) -> float:
    if not ground_truth_ids:
        return 1.0
    top_k = retrieved_ids[:k]
    relevant_retrieved = sum(1 for item in top_k if item in ground_truth_ids)
    return round(relevant_retrieved / len(ground_truth_ids), 4)

def reciprocal_rank(retrieved_ids: List[str], ground_truth_ids: Set[str]) -> float:
    for idx, item in enumerate(retrieved_ids, 1):
        if item in ground_truth_ids:
            return round(1.0 / idx, 4)
    return 0.0

def mean_reciprocal_rank(all_retrieved: List[List[str]], all_ground_truth: List[Set[str]]) -> float:
    if not all_retrieved:
        return 0.0
    rr_scores = [
        reciprocal_rank(retrieved, gt)
        for retrieved, gt in zip(all_retrieved, all_ground_truth)
    ]
    return round(sum(rr_scores) / len(rr_scores), 4)

def calculate_f1(precision: float, recall: float) -> float:
    if precision + recall == 0:
        return 0.0
    return round(2 * (precision * recall) / (precision + recall), 4)
