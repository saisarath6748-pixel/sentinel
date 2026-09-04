"""
Scoring engine.

Takes detected clusters and computes a 0-1 suspicion score per cluster.
Score combines:
  1. Signal overlap   (more shared signal types = more suspicious)
  2. Cluster size     (larger ring = more suspicious)
  3. Timing tightness (accounts created in a short window = more suspicious)
  4. Behavioral abuse (high promo usage + high refund rate = more suspicious)

Deterministic, no LLM involvement.
"""

import math
import pandas as pd

# Weights for score components
W_SIGNAL  = 0.30   # how many signal types are shared
W_SIZE    = 0.15   # cluster member count
W_TIMING  = 0.35   # signup window tightness
W_BEHAV   = 0.20   # promo + refund abuse rate

# Default review threshold
DEFAULT_THRESHOLD = 0.40


def _timing_score(signup_times: pd.Series) -> float:
    """
    Exponential decay based on signup time span.
    Tight window (< 1 day) -> ~1.0
    3 days -> ~0.55
    7 days -> ~0.25
    30 days -> ~0.002
    """
    if len(signup_times) < 2:
        return 0.5
    span_days = (signup_times.max() - signup_times.min()).total_seconds() / 86400.0
    return math.exp(-span_days / 3.0)


def _behavior_score(orders_df: pd.DataFrame, account_ids: frozenset[str]) -> float:
    """
    Score based on promo usage rate and refund request rate
    among the cluster's orders.
    """
    cluster_orders = orders_df[orders_df["account_id"].isin(account_ids)]
    if len(cluster_orders) == 0:
        return 0.0

    promo_rate = (cluster_orders["promo_code_used"].astype(str).str.len() > 0).mean()
    refund_rate = cluster_orders["refund_requested"].mean()

    # Weighted blend: promo abuse matters more than refund alone
    return float(promo_rate * 0.6 + refund_rate * 0.4)


def score_cluster(
    account_ids: frozenset[str],
    shared_signals: set[str],
    accounts_df: pd.DataFrame,
    orders_df: pd.DataFrame,
) -> dict:
    """
    Score a single cluster. Returns a dict with score breakdown.
    """
    # 1. Signal overlap score
    signal_score = len(shared_signals) / 3.0

    # 2. Size score (capped at 10 members)
    size_score = min(len(account_ids) / 10.0, 1.0)

    # 3. Timing tightness
    cluster_accts = accounts_df[accounts_df["account_id"].isin(account_ids)]
    timing = _timing_score(pd.to_datetime(cluster_accts["signup_time"], format='mixed'))

    # 4. Behavioral abuse
    behavior = _behavior_score(orders_df, account_ids)

    # Weighted total
    total = (
        W_SIGNAL * signal_score
        + W_SIZE * size_score
        + W_TIMING * timing
        + W_BEHAV * behavior
    )
    total = round(min(total, 1.0), 4)

    return {
        "account_ids": sorted(account_ids),
        "shared_signals": sorted(shared_signals),
        "num_accounts": len(account_ids),
        "score": total,
        "breakdown": {
            "signal_overlap": round(signal_score, 4),
            "cluster_size": round(size_score, 4),
            "timing_tightness": round(timing, 4),
            "behavior_abuse": round(behavior, 4),
        },
    }


def score_all_clusters(
    clusters: dict[frozenset[str], set[str]],
    accounts_df: pd.DataFrame,
    orders_df: pd.DataFrame,
    threshold: float = DEFAULT_THRESHOLD,
) -> list[dict]:
    """
    Score all clusters and return sorted by score (descending).
    Attaches a cluster_id label and flags those above the review threshold.
    """
    scored = []
    for i, (ids, sigs) in enumerate(clusters.items()):
        result = score_cluster(ids, sigs, accounts_df, orders_df)
        result["cluster_id"] = f"detected_{i:03d}"
        result["flagged_for_review"] = result["score"] >= threshold
        scored.append(result)

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def get_flagged_clusters(
    scored_clusters: list[dict],
    threshold: float = DEFAULT_THRESHOLD,
) -> list[dict]:
    """Return only clusters above the review threshold."""
    return [c for c in scored_clusters if c["score"] >= threshold]


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from detection.signals import load_accounts, load_orders, extract_account_signals
    from detection.cluster import find_clusters, merge_overlapping_clusters

    print("=" * 60)
    print("  Detection Engine - Full Pipeline Test")
    print("=" * 60)

    # Load data
    accts_df = load_accounts()
    orders_df = load_orders()
    signals_df = extract_account_signals(accts_df)

    # Cluster
    raw = find_clusters(signals_df)
    merged = merge_overlapping_clusters(raw)
    print(f"\nClusters found: {len(raw)} raw, {len(merged)} after merge")

    # Score
    scored = score_all_clusters(merged, accts_df, orders_df)
    flagged = get_flagged_clusters(scored)

    print(f"Total scored clusters: {len(scored)}")
    print(f"Flagged for review (>= {DEFAULT_THRESHOLD}): {len(flagged)}")

    print(f"\n  {'Cluster':<16} {'Score':>6}  {'Size':>4}  {'Flagged':>7}  Shared Signals")
    print(f"  {'-'*16} {'-'*6}  {'-'*4}  {'-'*7}  {'-'*30}")
    for c in scored:
        flag = "YES" if c["flagged_for_review"] else "no"
        sigs = ", ".join(c["shared_signals"])
        print(f"  {c['cluster_id']:<16} {c['score']:>6.4f}  {c['num_accounts']:>4}  {flag:>7}  {sigs}")

    print(f"\n  Score breakdown for top cluster:")
    top = scored[0]
    for k, v in top["breakdown"].items():
        print(f"    {k:<20}: {v:.4f}")
