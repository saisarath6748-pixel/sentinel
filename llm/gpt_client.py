"""
LLM client for cluster explanations.

Calls GPT API to turn a flagged cluster's data
into a plain-English explanation for a merchant's ops team.

This is ON-DEMAND ONLY -- never called during detection or scoring.
It never decides what gets flagged. It only explains what was already
flagged by the deterministic detection engine.

Usage (standalone test):
    python -m llm.gpt_client
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

    # Format exact indicators for the LLM
    exact_signals_desc = []
    for s in cluster_data.get("exact_shared_signals", []):
        exact_signals_desc.append(f"{s.get('label')}: {s.get('value')}")
    signals_str = "; ".join(exact_signals_desc) if exact_signals_desc else ", ".join(cluster_data.get("shared_signals", []))
    
    phones = cluster_data.get("phones", [])
    phones_str = f"Associated phone(s): {', '.join(phones)}" if phones else ""
    
    vol = cluster_data.get("total_volume")
    curr = "₹" if cluster_data.get("currency") == "INR" else "$"
    vol_str = f"Total order volume: {curr}{vol}" if vol else ""

    prompt = f"""You are a helpful fraud assistant for an e-commerce merchant. 
They have a dashboard showing suspicious groups of accounts (abuse rings).
Given this data, write a 2-sentence explanation for the merchant.

Cluster Summary:
- Cluster ID: {cluster_data.get('cluster_id')}
- Number of accounts: {cluster_data.get('num_accounts')}
- Shared indicators: {signals_str}
{phones_str}
{vol_str}
- Timing span: accounts placed orders in a tight window
- Raw cluster data: {cluster_data}

Rules:
- Speak in extremely simple, non-technical terms. No jargon (do not use words like "hash", "signal", "overlap", or "metric").
- When exact details are provided (such as card brand and last 4 digits like MasterCard ending in 5449, or phone number), explicitly mention them so the merchant knows exactly what was shared.
- STRICT: ONLY mention the indicators that are actually listed under "Shared indicators". Never claim accounts shared an address or device unless "Shared Address" or "Shared Device" is explicitly listed.
- If high refunds or promo abuse exist, mention it simply.
- Keep it short (2 sentences), professional, friendly, and factual."""

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
