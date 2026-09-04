"""
FastAPI routes for Abuse-Ring Sentinel.

Endpoints:
  POST /auth/login                   -> authenticate via local SQLite + JWT
  GET  /auth/me                      -> current merchant profile
  PUT  /auth/profile                 -> update name, password, avatar
  GET  /clusters                     -> all scored clusters (deterministic, no LLM)
  GET  /clusters/flagged             -> only clusters above review threshold
  GET  /clusters/{cluster_id}/explain -> LLM explanation (on-demand)
  POST /clusters/refresh             -> re-run detection pipeline
  GET  /razorpay/payments            -> recent Razorpay test-mode payments
  POST /scan                         -> key leak scanner
  GET  /health                       -> health check
"""

import importlib
import sys
import os
import base64
import uuid
import secrets
import hashlib
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

import bcrypt
import jwt

from detection.signals import load_accounts, load_orders, extract_account_signals
from detection.cluster import find_clusters, merge_overlapping_clusters
from detection.score import score_all_clusters, get_flagged_clusters, DEFAULT_THRESHOLD
from llm.explain_cluster import get_explanation

# ---------------------------------------------------------------------------
# JWT config
# ---------------------------------------------------------------------------
from dotenv import load_dotenv
load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", secrets.token_hex(32))
JWT_ALGORITHM = "HS256"

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Abuse-Ring Sentinel API",
    description="Detects coordinated buyer-side abuse rings across merchants",
    version="1.0.0",
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded avatars as static files
UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
os.makedirs(os.path.join(UPLOADS_DIR, "avatars"), exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: str
    password: str

class ProfileUpdateRequest(BaseModel):
    name: str
    password: str | None = None
    avatar_data: str | None = None
    avatar_filename: str | None = None

class ScanRequest(BaseModel):
    repo_path: str
    scan_history: bool = False

# ---------------------------------------------------------------------------
# Cache detection results (recomputed on startup or on-demand)
# ---------------------------------------------------------------------------
_scored_clusters: list[dict] = []
_accounts_df = None


def _run_detection():
    """Run the full detection pipeline and cache results."""
    global _scored_clusters, _accounts_df
    _accounts_df = load_accounts()
    orders_df = load_orders()
    signals_df = extract_account_signals(_accounts_df)
    raw = find_clusters(signals_df)
    merged = merge_overlapping_clusters(raw)
    _scored_clusters = score_all_clusters(merged, _accounts_df, orders_df)

    # Attach merchant_id to each cluster by looking up its accounts
    for cluster in _scored_clusters:
        acct_ids = cluster["account_ids"]
        merchants = _accounts_df[_accounts_df["account_id"].isin(acct_ids)]["merchant_id"].unique()
        cluster["merchant_id"] = str(merchants[0]) if len(merchants) > 0 else None


@app.on_event("startup")
def startup():
    # Initialize database and seed demo accounts
    from db.database import init_db
    from db.seed import seed
    init_db()
    seed()

    # If Gamma Groceries has no records in CSV, auto-ingest from Razorpay test mode
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        accounts_file = os.path.join(base_dir, "data", "accounts.csv")
        if os.path.exists(accounts_file):
            df_accs = pd.read_csv(accounts_file)
            gamma_exists = (df_accs["merchant_id"] == "1ed1d417-6ce7-4b1d-ba96-1a08097b591a").any()
            if not gamma_exists:
                _ingest_razorpay("1ed1d417-6ce7-4b1d-ba96-1a08097b591a")
    except Exception as e:
        print(f"Startup Razorpay ingestion warning: {e}")

    # Run detection pipeline
    _run_detection()


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def _create_token(merchant_id: str) -> str:
    return jwt.encode({"sub": merchant_id}, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _verify_token(authorization: str = "") -> str:
    """Extract and verify JWT from Authorization header. Returns merchant_id."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.post("/auth/login")
def login(req: LoginRequest):
    """Authenticate a merchant via local SQLite + bcrypt."""
    from db.database import get_merchant_by_email

    merchant = get_merchant_by_email(req.email)
    if not merchant:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not bcrypt.checkpw(req.password.encode(), merchant["password_hash"].encode()):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = _create_token(merchant["id"])

    return {
        "user": {
            "id": merchant["id"],
            "email": merchant["email"],
        },
        "access_token": token,
        "merchant_name": merchant["name"],
        "avatar_url": merchant.get("avatar_url"),
    }


@app.get("/auth/me")
def get_me(authorization: str = Header("")):
    """Validate JWT and return current merchant profile."""
    merchant_id = _verify_token(authorization)

    from db.database import get_merchant_by_id
    merchant = get_merchant_by_id(merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")

    return {
        "user": {
            "id": merchant["id"],
            "email": merchant["email"],
        },
        "merchant_name": merchant["name"],
        "avatar_url": merchant.get("avatar_url"),
    }


@app.put("/auth/profile")
def update_profile(req: ProfileUpdateRequest, authorization: str = Header("")):
    """Update merchant name, password, and/or avatar."""
    merchant_id = _verify_token(authorization)

    from db.database import get_merchant_by_id, update_merchant
    merchant = get_merchant_by_id(merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")

    update_data = {"name": req.name}

    # Update password if provided
    if req.password:
        pw_hash = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode()
        update_data["password_hash"] = pw_hash

    # Save avatar locally if provided
    avatar_url = None
    if req.avatar_data and req.avatar_filename:
        try:
            header, encoded = req.avatar_data.split(",", 1) if "," in req.avatar_data else ("", req.avatar_data)
            file_bytes = base64.b64decode(encoded)

            ext = os.path.splitext(req.avatar_filename)[1]
            if not ext:
                ext = ".png"

            file_name = f"{merchant_id}-{uuid.uuid4().hex[:8]}{ext}"
            file_path = os.path.join(UPLOADS_DIR, "avatars", file_name)

            with open(file_path, "wb") as f:
                f.write(file_bytes)

            avatar_url = f"http://localhost:8000/uploads/avatars/{file_name}"
            update_data["avatar_url"] = avatar_url
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Avatar upload failed: {str(e)}")

    update_merchant(merchant_id, update_data)

    return {"status": "success", "avatar_url": avatar_url}


# ---------------------------------------------------------------------------
# Detection routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "clusters_loaded": len(_scored_clusters)}


@app.get("/clusters")
def get_clusters(merchant_id: str | None = Query(None)):
    """Return all scored clusters, optionally filtered by merchant_id."""
    clusters = _scored_clusters
    if merchant_id:
        clusters = [c for c in clusters if c.get("merchant_id") == merchant_id]
    return {"clusters": clusters, "total": len(clusters)}


@app.get("/clusters/flagged")
def get_flagged(merchant_id: str | None = Query(None)):
    """Return only clusters above the review threshold, optionally filtered."""
    flagged = get_flagged_clusters(_scored_clusters)
    if merchant_id:
        flagged = [c for c in flagged if c.get("merchant_id") == merchant_id]
    return {"clusters": flagged, "total": len(flagged), "threshold": DEFAULT_THRESHOLD}


@app.get("/clusters/{cluster_id}/explain")
def explain(cluster_id: str):
    """
    Generate an LLM explanation for a specific cluster.
    This is the ONLY endpoint that calls the LLM -- on demand, not during detection.
    """
    cluster = next((c for c in _scored_clusters if c["cluster_id"] == cluster_id), None)
    if not cluster:
        raise HTTPException(status_code=404, detail=f"Cluster '{cluster_id}' not found")

    try:
        explanation = get_explanation(cluster)
        return {"cluster_id": cluster_id, "explanation": explanation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")


@app.post("/clusters/refresh")
def refresh():
    """Re-run the detection pipeline (e.g. after new data ingestion)."""
    _run_detection()
    return {"status": "refreshed", "clusters_loaded": len(_scored_clusters)}


def _ingest_razorpay(merchant_id: str):
    """Fetch recent test payments from Razorpay and map them into the Sentinel detection schema."""
    from ingestion.razorpay_client import fetch_recent_payments
    payments = fetch_recent_payments()
    if not payments:
        return {"status": "success", "added_accounts": 0, "added_orders": 0, "total_clusters": len(_scored_clusters)}

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    accounts_file = os.path.join(base_dir, "data", "accounts.csv")
    orders_file = os.path.join(base_dir, "data", "orders.csv")

    new_accounts = []
    new_orders = []

    for p in payments:
        email = p.get("email") or "unknown@example.com"
        contact = p.get("contact") or "0000000000"
        card_id = p.get("card_id") or "card_unknown"

        # Unique account ID per payment transaction to model multi-account card-testing & abuse rings
        acc_id = f"acct_rzp_{p['payment_id'][-8:]}"

        # Deterministic hashes for simulated signals based on Razorpay data
        device_hash = hashlib.md5(str(contact).encode()).hexdigest()[:16]
        address_hash = hashlib.md5((str(contact) + "addr").encode()).hexdigest()[:16]
        card_hash = hashlib.md5(str(card_id).encode()).hexdigest()[:16]

        new_accounts.append({
            "account_id": acc_id,
            "merchant_id": merchant_id,
            "email": email,
            "phone": contact,
            "device_hash": device_hash,
            "address_hash": address_hash,
            "card_hash": card_hash,
            "signup_time": p.get("created_at") or datetime.now().isoformat()
        })

        new_orders.append({
            "order_id": p.get("payment_id"),
            "account_id": acc_id,
            "merchant_id": merchant_id,
            "amount": p.get("amount"),
            "promo_code_used": "",
            "refund_requested": p.get("status") in ["refunded", "failed"],
            "order_time": p.get("created_at") or datetime.now().isoformat()
        })

    df_new_accs = pd.DataFrame(new_accounts).drop_duplicates(subset=["account_id"])
    df_new_ords = pd.DataFrame(new_orders).drop_duplicates(subset=["order_id"])

    # Overwrite previous Gamma Groceries records to keep data clean and synchronized
    if os.path.exists(accounts_file):
        df_accs = pd.read_csv(accounts_file)
        df_accs = df_accs[df_accs["merchant_id"] != merchant_id]
        df_accs = pd.concat([df_accs, df_new_accs], ignore_index=True)
        df_accs.to_csv(accounts_file, index=False)
    else:
        df_new_accs.to_csv(accounts_file, index=False)

    if os.path.exists(orders_file):
        df_ords = pd.read_csv(orders_file)
        df_ords = df_ords[df_ords["merchant_id"] != merchant_id]
        df_ords = pd.concat([df_ords, df_new_ords], ignore_index=True)
        df_ords.to_csv(orders_file, index=False)
    else:
        df_new_ords.to_csv(orders_file, index=False)

    _run_detection()

    return {
        "status": "success",
        "added_accounts": len(df_new_accs),
        "added_orders": len(df_new_ords),
        "total_clusters": len(_scored_clusters)
    }


@app.post("/razorpay/ingest")
def razorpay_ingest(authorization: str = Header("")):
    """Fetch recent payments from Razorpay test mode and append to CSVs."""
    merchant_id = _verify_token(authorization)

    # 1ed1d417-6ce7-4b1d-ba96-1a08097b591a is Gamma Groceries
    if merchant_id != "1ed1d417-6ce7-4b1d-ba96-1a08097b591a":
        raise HTTPException(
            status_code=403,
            detail="Test mode payments sync is only enabled for Gamma Groceries. The other demo accounts use synthetic data."
        )

    try:
        return _ingest_razorpay(merchant_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Razorpay ingestion error: {str(e)}")


@app.get("/razorpay/payments")
def get_razorpay_payments(authorization: str = Header("")):
    """Fetch recent payments from Razorpay test mode enriched with abuse ring status."""
    merchant_id = _verify_token(authorization)

    # 1ed1d417-6ce7-4b1d-ba96-1a08097b591a is Gamma Groceries
    if merchant_id != "1ed1d417-6ce7-4b1d-ba96-1a08097b591a":
        raise HTTPException(
            status_code=403,
            detail="Test mode payments sync is only enabled for Gamma Groceries. The other demo accounts use synthetic data."
        )

    try:
        from ingestion.razorpay_client import fetch_recent_payments
        payments = fetch_recent_payments()

        # Check which account IDs belong to flagged clusters for Gamma
        gamma_clusters = [c for c in _scored_clusters if c.get("merchant_id") == merchant_id]
        flagged_acct_to_cluster = {}
        for c in gamma_clusters:
            if c.get("flagged_for_review"):
                for aid in c.get("account_ids", []):
                    flagged_acct_to_cluster[aid] = c.get("cluster_id")

        enriched = []
        for p in payments:
            acc_id = f"acct_rzp_{p['payment_id'][-8:]}"
            cluster_id = flagged_acct_to_cluster.get(acc_id)
            enriched.append({
                **p,
                "account_id": acc_id,
                "is_flagged_ring": cluster_id is not None,
                "cluster_id": cluster_id,
            })

        return {
            "status": "success",
            "payments": enriched,
            "total": len(enriched),
            "flagged_count": sum(1 for item in enriched if item["is_flagged_ring"])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch Razorpay payments: {str(e)}")


# ---------------------------------------------------------------------------
# Key Scanner route
# ---------------------------------------------------------------------------

def _load_scanner():
    """Import scanner module (key-scanner has a hyphen, can't import normally)."""
    scanner_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "key-scanner"
    )
    if scanner_dir not in sys.path:
        sys.path.insert(0, scanner_dir)

    spec = importlib.util.spec_from_file_location(
        "scanner",
        os.path.join(scanner_dir, "scanner.py")
    )
    scanner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scanner)
    return scanner


@app.post("/scan")
def scan_repo(req: ScanRequest):
    """Run the key leak scanner against a local repository path."""
    repo_path = os.path.abspath(req.repo_path)

    if not os.path.isdir(repo_path):
        raise HTTPException(
            status_code=400,
            detail=f"'{req.repo_path}' is not a valid directory"
        )

    try:
        scanner = _load_scanner()
        findings = []

        # 1. Check .gitignore
        findings.extend(scanner.check_gitignore(repo_path))

        # 2. Scan working tree
        findings.extend(scanner.scan_working_tree(repo_path))

        # 3. Optionally scan git history
        if req.scan_history:
            findings.extend(scanner.scan_git_history(repo_path))

        # Sort by confidence (highest first)
        findings.sort(key=lambda f: f["confidence"], reverse=True)

        # Summary
        high = sum(1 for f in findings if f["confidence"] >= 0.85)
        medium = sum(1 for f in findings if 0.60 <= f["confidence"] < 0.85)
        low = sum(1 for f in findings if f["confidence"] < 0.60)

        return {
            "findings": findings,
            "total": len(findings),
            "scanned_path": repo_path,
            "summary": {"high": high, "medium": medium, "low": low},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scanner error: {str(e)}")
