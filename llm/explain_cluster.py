"""
Cluster explanation module.

Wraps gpt_client.explain_cluster() with caching and error handling.
Used by the API route /clusters/{id}/explain.
"""

from llm.gpt_client import explain_cluster

# Simple in-memory cache to avoid re-calling the LLM for the same cluster
_cache: dict[str, str] = {}


def get_explanation(cluster_data: dict) -> str:
    """
    Get or generate an explanation for a cluster.
    Caches results by cluster_id to avoid redundant LLM calls.
    """
    cluster_id = cluster_data.get("cluster_id", "")

    if cluster_id in _cache:
        return _cache[cluster_id]

    explanation = explain_cluster(cluster_data)
    if cluster_id:
        _cache[cluster_id] = explanation

    return explanation


def clear_cache():
    """Clear the explanation cache."""
    _cache.clear()
