"""
Clustering engine.

Groups accounts by shared signal values (device, address, card hash).
Uses simple groupby approach per the brief's reference implementation.
Deterministic, no LLM involvement.
"""

from collections import defaultdict
import pandas as pd

SIGNAL_COLUMNS = ["device_hash", "address_hash", "card_hash"]


def find_clusters(
    accounts_df: pd.DataFrame,
    min_size: int = 3,
) -> dict[frozenset[str], set[str]]:
    """
    Find clusters of accounts sharing signal values.

    For each signal column, groups accounts by that signal's value.
    Any group with >= min_size accounts becomes a cluster.
    If two signal columns produce the exact same set of account IDs,
    they merge into one cluster entry (the frozenset key deduplicates).

    Returns:
        dict mapping frozenset(account_ids) -> set(signal_column_names)
    """
    clusters: dict[frozenset[str], set[str]] = defaultdict(set)

    for signal_col in SIGNAL_COLUMNS:
        groups = accounts_df.groupby(signal_col)["account_id"].apply(list)
        for ids in groups:
            if len(ids) >= min_size:
                key = frozenset(ids)
                clusters[key].add(signal_col)

    return dict(clusters)


def merge_overlapping_clusters(
    clusters: dict[frozenset[str], set[str]],
) -> dict[frozenset[str], set[str]]:
    """
    Merge clusters that share any account IDs (connected-component merge).
    This catches cases where group A shares device_hash and group B shares
    card_hash, but they overlap in membership.

    Uses iterative union until stable.
    """
    cluster_list = [(set(ids), sigs) for ids, sigs in clusters.items()]
    merged = True

    while merged:
        merged = False
        new_list = []
        used = [False] * len(cluster_list)

        for i in range(len(cluster_list)):
            if used[i]:
                continue
            current_ids, current_sigs = cluster_list[i]
            for j in range(i + 1, len(cluster_list)):
                if used[j]:
                    continue
                other_ids, other_sigs = cluster_list[j]
                if current_ids & other_ids:  # overlap
                    current_ids |= other_ids
                    current_sigs |= other_sigs
                    used[j] = True
                    merged = True
            new_list.append((current_ids, current_sigs))
            used[i] = True

        cluster_list = new_list

    return {frozenset(ids): sigs for ids, sigs in cluster_list}


if __name__ == "__main__":
    from detection.signals import load_accounts, extract_account_signals

    accts = load_accounts()
    signals_df = extract_account_signals(accts)

    raw_clusters = find_clusters(signals_df)
    merged = merge_overlapping_clusters(raw_clusters)

    print(f"Raw clusters found:    {len(raw_clusters)}")
    print(f"After merging overlaps: {len(merged)}")
    print()
    for i, (ids, sigs) in enumerate(sorted(merged.items(), key=lambda x: -len(x[0]))):
        print(f"  Cluster {i+1:>2}: {len(ids)} accounts, shared: {', '.join(sorted(sigs))}")
