"""
Evaluation harness for Abuse-Ring Sentinel.

Runs the full detection pipeline against ground_truth.json and reports
precision, recall, F1, TP, FP, FN with detailed match explanations.

Matching logic (from brief section 7):
  - TP: a ground-truth fraud ring whose account set is a SUBSET of some
        predicted (flagged) cluster
  - FN: a ground-truth fraud ring that no predicted cluster fully contains
  - FP: a predicted cluster that does not overlap with ANY ground-truth
        fraud ring (i.e. it caught an innocent cluster, or a spurious group)

Only clusters that pass the review threshold are counted as predictions.

Usage:  python eval/evaluate.py
        python -m eval.evaluate
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from detection.signals import load_accounts, load_orders, extract_account_signals
from detection.cluster import find_clusters, merge_overlapping_clusters
from detection.score import score_all_clusters, DEFAULT_THRESHOLD

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def load_ground_truth(path: str | None = None) -> list[dict]:
    p = path or os.path.join(DATA_DIR, "ground_truth.json")
    with open(p) as f:
        return json.load(f)


def evaluate(
    predicted_clusters: list[set[str]],
    ground_truth: list[dict],
) -> dict:
    """
    Evaluate predicted clusters against ground truth.
    Uses the reference logic from brief section 7.

    Args:
        predicted_clusters: list of sets of account_ids (only flagged ones)
        ground_truth: list of dicts with cluster_id, account_ids, is_fraud_ring

    Returns:
        dict with precision, recall, f1, tp, fp, fn, and detailed match info
    """
    tp = fp = fn = 0
    tp_details = []
    fn_details = []
    fp_details = []

    # --- TP / FN: check each ground-truth fraud ring ---
    for gt in ground_truth:
        if not gt["is_fraud_ring"]:
            continue

        gt_set = set(gt["account_ids"])
        matched_pred = None

        for pred in predicted_clusters:
            if gt_set <= pred:  # GT is a subset of prediction
                matched_pred = pred
                break

        if matched_pred is not None:
            tp += 1
            tp_details.append({
                "gt_cluster": gt["cluster_id"],
                "gt_accounts": sorted(gt_set),
                "pred_accounts": sorted(matched_pred),
                "exact_match": gt_set == matched_pred,
            })
        else:
            fn += 1
            # Find best partial overlap for diagnostic
            best_overlap = 0
            best_pred = None
            for pred in predicted_clusters:
                overlap = len(gt_set & pred)
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_pred = pred
            fn_details.append({
                "gt_cluster": gt["cluster_id"],
                "gt_size": len(gt_set),
                "best_overlap": best_overlap,
                "gt_accounts": sorted(gt_set),
            })

    # --- FP: predicted clusters not overlapping any fraud ring ---
    fraud_rings = [gt for gt in ground_truth if gt["is_fraud_ring"]]
    for pred in predicted_clusters:
        overlaps_real_ring = any(
            pred & set(gt["account_ids"]) for gt in fraud_rings
        )
        if not overlaps_real_ring:
            fp += 1
            # Check if it matches an innocent cluster
            matched_innocent = None
            for gt in ground_truth:
                if not gt["is_fraud_ring"] and set(gt["account_ids"]) <= pred:
                    matched_innocent = gt["cluster_id"]
                    break
            fp_details.append({
                "pred_accounts": sorted(pred),
                "pred_size": len(pred),
                "matched_innocent_cluster": matched_innocent,
            })

    # --- Metrics ---
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "total_gt_fraud_rings": len(fraud_rings),
        "total_gt_innocent": len([g for g in ground_truth if not g["is_fraud_ring"]]),
        "total_predictions": len(predicted_clusters),
        "tp_details": tp_details,
        "fn_details": fn_details,
        "fp_details": fp_details,
    }


def run_full_eval(threshold: float = DEFAULT_THRESHOLD) -> dict:
    """
    End-to-end: load data -> detect -> score -> evaluate against ground truth.
    Returns eval results dict.
    """
    # Load
    accts_df = load_accounts()
    orders_df = load_orders()
    signals_df = extract_account_signals(accts_df)
    gt = load_ground_truth()

    # Detect + score
    raw_clusters = find_clusters(signals_df)
    merged = merge_overlapping_clusters(raw_clusters)
    scored = score_all_clusters(merged, accts_df, orders_df, threshold=threshold)

    # Only flagged clusters count as predictions
    flagged = [c for c in scored if c["flagged_for_review"]]
    predicted_sets = [set(c["account_ids"]) for c in flagged]

    # Evaluate
    results = evaluate(predicted_sets, gt)
    results["threshold"] = threshold
    results["scored_clusters"] = scored  # attach for reporting

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("  Abuse-Ring Sentinel - Evaluation Harness")
    print("=" * 60)

    results = run_full_eval()

    # --- Summary ---
    print(f"\n  EVALUATION RESULTS  (threshold = {results['threshold']})")
    print(f"  {'-'*50}")
    print(f"  Ground truth fraud rings:   {results['total_gt_fraud_rings']}")
    print(f"  Ground truth innocent:      {results['total_gt_innocent']}")
    print(f"  Predicted clusters:         {results['total_predictions']}")
    print(f"  {'-'*50}")
    print(f"  True Positives  (TP):       {results['tp']}")
    print(f"  False Positives (FP):       {results['fp']}")
    print(f"  False Negatives (FN):       {results['fn']}")
    print(f"  {'-'*50}")
    print(f"  Precision:                  {results['precision']:.4f}")
    print(f"  Recall:                     {results['recall']:.4f}")
    print(f"  F1 Score:                   {results['f1']:.4f}")
    print(f"  {'-'*50}")

    # --- TP details ---
    if results["tp_details"]:
        print(f"\n  TRUE POSITIVES ({results['tp']}):")
        for d in results["tp_details"]:
            exact = " (exact)" if d["exact_match"] else f" (superset: {len(d['pred_accounts'])} accts)"
            print(f"    {d['gt_cluster']}: {len(d['gt_accounts'])} accounts matched{exact}")

    # --- FN details ---
    if results["fn_details"]:
        print(f"\n  FALSE NEGATIVES ({results['fn']}):")
        for d in results["fn_details"]:
            print(f"    {d['gt_cluster']}: {d['gt_size']} accounts, best overlap = {d['best_overlap']}")

    # --- FP details ---
    if results["fp_details"]:
        print(f"\n  FALSE POSITIVES ({results['fp']}):")
        for d in results["fp_details"]:
            inno = f" -> innocent cluster: {d['matched_innocent_cluster']}" if d["matched_innocent_cluster"] else ""
            print(f"    {d['pred_size']} accounts{inno}")

    # --- False positive cost note ---
    if results["fp"] == 0:
        print(f"\n  [NOTE] Zero false positives. The scoring threshold ({results['threshold']})")
        print(f"  cleanly separates fraud rings from innocent clusters in this")
        print(f"  synthetic dataset. Real-world data would likely produce some FPs.")
        print(f"  See scored cluster list for the score gap between lowest fraud")
        print(f"  ring and highest innocent cluster.")

    # --- Score distribution ---
    scored = results["scored_clusters"]
    flagged_scores = [c["score"] for c in scored if c["flagged_for_review"]]
    unflagged_scores = [c["score"] for c in scored if not c["flagged_for_review"]]

    print(f"\n  SCORE DISTRIBUTION")
    print(f"  {'-'*50}")
    if flagged_scores:
        print(f"  Flagged   (n={len(flagged_scores):>2}): "
              f"min={min(flagged_scores):.4f}  max={max(flagged_scores):.4f}  "
              f"mean={sum(flagged_scores)/len(flagged_scores):.4f}")
    if unflagged_scores:
        print(f"  Unflagged (n={len(unflagged_scores):>2}): "
              f"min={min(unflagged_scores):.4f}  max={max(unflagged_scores):.4f}  "
              f"mean={sum(unflagged_scores)/len(unflagged_scores):.4f}")
    if flagged_scores and unflagged_scores:
        gap = min(flagged_scores) - max(unflagged_scores)
        print(f"  Score gap:         {gap:.4f}")
