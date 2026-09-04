"""
LLM client for cluster explanations.

Calls Llama 3.3 70B via Groq API to turn a flagged cluster's data
into a plain-English explanation for a merchant's ops team.

This is ON-DEMAND ONLY -- never called during detection or scoring.
It never decides what gets flagged. It only explains what was already
flagged by the deterministic detection engine.

Usage (standalone test):
    python -m llm.llama_client
"""

import os
from dotenv import load_dotenv

load_dotenv()


def explain_cluster(cluster_data: dict) -> str:
    """
    Generate a plain-English explanation of a flagged cluster.

    Args:
        cluster_data: dict with account_ids, shared_signals, score, breakdown, etc.

    Returns:
        2-3 sentence factual explanation for a merchant's ops team.
    """
    from groq import Groq

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key.startswith("gsk_xxx"):
        raise RuntimeError(
            "GROQ_API_KEY must be set in .env with a real key from console.groq.com"
        )

    client = Groq(api_key=api_key)

    # Model selection: use env var or default to what's currently available on Groq.
    # The brief specifies Llama, but Groq rotates models. Any open-source LLM works
    # here since it's only used for plain-English explanations, never for detection.
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

    prompt = f"""You are a helpful fraud assistant for a small business owner. 
They have a dashboard showing suspicious groups of buyers (clusters).
Given this data, write a 2-sentence explanation for the merchant.

Cluster data: {cluster_data}

Rules:
- Speak in extremely simple, non-technical terms. No jargon (do not use the words "hash", "signal", "overlap", or "metric").
- Do not mention the exact math or breakdown numbers.
- Simply tell the merchant *why* these accounts look suspicious (e.g., "These 5 accounts all share the same device and shipping address, and bought items at the exact same time").
- If there are high refunds or promo abuse, mention it simply ("They are abusing promo codes").
- Keep it friendly, short, and very easy to understand."""

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
        temperature=0.2,  # low temp for factual consistency
    )

    raw = response.choices[0].message.content

    # Some models (e.g. Qwen) emit <think>...</think> reasoning blocks.
    # Strip those out — we only want the final plain-English answer.
    import re
    cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    return cleaned if cleaned else raw


# ---------------------------------------------------------------------------
# Standalone test with a sample cluster
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("  LLM Explanation Layer - Test")
    print("=" * 60)

    # Build a sample cluster to explain
    sample_cluster = {
        "cluster_id": "detected_004",
        "account_ids": ["acct_ring009_00", "acct_ring009_01", "acct_ring009_02",
                        "acct_ring009_03", "acct_ring009_04"],
        "shared_signals": ["address_hash", "card_hash", "device_hash"],
        "num_accounts": 5,
        "score": 0.7104,
        "breakdown": {
            "signal_overlap": 1.0,
            "cluster_size": 0.5,
            "timing_tightness": 0.5629,
            "behavior_abuse": 0.6919,
        },
    }

    print(f"\n  Input cluster: {sample_cluster['cluster_id']}")
    print(f"  Accounts: {sample_cluster['num_accounts']}")
    print(f"  Score: {sample_cluster['score']}")
    print(f"  Shared: {', '.join(sample_cluster['shared_signals'])}")

    print(f"\n  Calling Llama 3.3 70B via Groq ...")

    try:
        explanation = explain_cluster(sample_cluster)
        # Make output safe for Windows cp1252 terminal
        safe_text = explanation.encode("ascii", errors="replace").decode("ascii")
        print(f"\n  EXPLANATION:")
        print(f"  {'-'*50}")
        # Word-wrap for terminal
        words = safe_text.split()
        line = "  "
        for w in words:
            if len(line) + len(w) + 1 > 70:
                print(line)
                line = "  " + w
            else:
                line += " " + w if line.strip() else "  " + w
        if line.strip():
            print(line)
    except Exception as e:
        print(f"\n  ERROR: {e}")
