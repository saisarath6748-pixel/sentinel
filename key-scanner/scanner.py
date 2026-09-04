"""
Key Leak Scanner - Standalone CLI tool

Scans a local repository for leaked API keys and secrets.
Fully independent of the sentinel detection/scoring pipeline.

Features:
  - Checks .gitignore coverage for common secret file patterns
  - Regex + entropy scan for key patterns (Razorpay, Supabase, Groq, etc.)
  - Optionally scans git history (not just working tree)
  - Outputs: file path, line number, confidence score, suggested fix

Usage:
    python key-scanner/scanner.py /path/to/repo
    python key-scanner/scanner.py /path/to/repo --history
    python key-scanner/scanner.py ./sample_repo        # demo with planted secrets

Access model (important for pitch):
    This tool ONLY reads files it is explicitly pointed at (a local path).
    It never reaches into a live backend server or production infrastructure.
    In production, this would run as a GitHub Action / CI step on every push.
"""

import argparse
import math
import os
import re
import subprocess
import sys
from pathlib import Path

# ──────────────────────────────────────────────────────────────
# 1. Key patterns: prefix-based regex for known providers
# ──────────────────────────────────────────────────────────────

KEY_PATTERNS = [
    {
        "name": "Razorpay Live Key",
        "regex": r"rzp_live_[A-Za-z0-9]{10,}",
        "confidence": 0.95,
        "fix": "Rotate immediately at https://dashboard.razorpay.com -> Settings -> API Keys. Add the file to .gitignore.",
    },
    {
        "name": "Razorpay Test Key",
        "regex": r"rzp_test_[A-Za-z0-9]{10,}",
        "confidence": 0.70,
        "fix": "This is a test key, but should still not be committed. Add the file to .gitignore and use environment variables.",
    },
    {
        "name": "Supabase Service Role Key (JWT)",
        "regex": r"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9\.eyJ[A-Za-z0-9_-]{50,}",
        "confidence": 0.90,
        "fix": "Rotate in Supabase Dashboard -> Settings -> API. Never expose service_role keys in frontend code.",
    },
    {
        "name": "Groq API Key",
        "regex": r"gsk_[A-Za-z0-9]{20,}",
        "confidence": 0.90,
        "fix": "Rotate at https://console.groq.com -> API Keys. Store in environment variables only.",
    },
    {
        "name": "AWS Access Key",
        "regex": r"AKIA[0-9A-Z]{16}",
        "confidence": 0.95,
        "fix": "Rotate in AWS IAM console immediately. Use IAM roles or environment variables instead.",
    },
    {
        "name": "Generic Private Key",
        "regex": r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
        "confidence": 0.99,
        "fix": "Remove the private key from the repository and regenerate it. Never commit private keys.",
    },
    {
        "name": "Google Service Account Key",
        "regex": r'"type"\s*:\s*"service_account"',
        "confidence": 0.95,
        "fix": "Remove google-services.json / key.json from the repo. Add to .gitignore.",
    },
]

# ──────────────────────────────────────────────────────────────
# 2. Files that should always be in .gitignore
# ──────────────────────────────────────────────────────────────

SECRET_FILE_PATTERNS = [
    ".env",
    ".env.local",
    ".env.production",
    ".env.*.local",
    "google-services.json",
    "key.json",
    "*.pem",
    "*.key",
    "serviceAccountKey.json",
]

# ──────────────────────────────────────────────────────────────
# 3. File extensions to skip (binaries, images, etc.)
# ──────────────────────────────────────────────────────────────

SKIP_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp",
    ".woff", ".woff2", ".ttf", ".eot",
    ".zip", ".tar", ".gz", ".rar",
    ".exe", ".dll", ".so", ".dylib",
    ".pyc", ".pyo", ".class",
    ".lock",
}

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".next", "dist", "build",
    ".venv", "venv", "env",
}

# ──────────────────────────────────────────────────────────────
# 4. Shannon entropy for generic high-entropy string detection
# ──────────────────────────────────────────────────────────────

def shannon_entropy(s: str) -> float:
    """Calculate Shannon entropy of a string."""
    if not s:
        return 0.0
    freq = {}
    for c in s:
        freq[c] = freq.get(c, 0) + 1
    length = len(s)
    return -sum((count / length) * math.log2(count / length) for count in freq.values())


def find_high_entropy_strings(line: str, threshold: float = 4.5, min_len: int = 20) -> list[dict]:
    """
    Find high-entropy strings in a line that might be secrets.
    Only flags strings that are long enough and random-looking.
    """
    findings = []
    # Look for quoted strings or assignment values
    patterns = [
        r'["\']([A-Za-z0-9+/=_-]{20,})["\']',   # quoted strings
        r'=\s*([A-Za-z0-9+/=_-]{20,})',           # env-style assignments
    ]
    for pat in patterns:
        for match in re.finditer(pat, line):
            candidate = match.group(1)
            if len(candidate) >= min_len:
                entropy = shannon_entropy(candidate)
                if entropy >= threshold:
                    findings.append({
                        "name": "High-Entropy String (potential secret)",
                        "matched": candidate[:40] + "..." if len(candidate) > 40 else candidate,
                        "confidence": min(0.60 + (entropy - threshold) * 0.1, 0.85),
                        "fix": "Verify this is not a secret. If it is, remove it and use environment variables.",
                    })
    return findings


# ──────────────────────────────────────────────────────────────
# 5. .gitignore checker
# ──────────────────────────────────────────────────────────────

def check_gitignore(repo_path: str) -> list[dict]:
    """Check if .gitignore exists and covers common secret patterns."""
    findings = []
    gitignore_path = os.path.join(repo_path, ".gitignore")

    if not os.path.exists(gitignore_path):
        findings.append({
            "file": ".gitignore",
            "line": 0,
            "name": "Missing .gitignore",
            "confidence": 1.0,
            "fix": "Create a .gitignore file and add patterns for .env, key files, and other secrets.",
        })
        return findings

    with open(gitignore_path, "r", errors="replace") as f:
        gitignore_content = f.read()

    for pattern in SECRET_FILE_PATTERNS:
        if pattern not in gitignore_content:
            # Check if the actual file exists (only warn if it does)
            if any(
                os.path.exists(os.path.join(repo_path, p))
                for p in [pattern, pattern.replace("*.", "test.")]
            ):
                findings.append({
                    "file": ".gitignore",
                    "line": 0,
                    "name": f"Missing .gitignore pattern: {pattern}",
                    "confidence": 0.80,
                    "fix": f"Add '{pattern}' to your .gitignore file.",
                })

    return findings


# ──────────────────────────────────────────────────────────────
# 6. File scanner (working tree)
# ──────────────────────────────────────────────────────────────

def scan_file(file_path: str, repo_root: str) -> list[dict]:
    """Scan a single file for key patterns and high-entropy strings."""
    findings = []
    rel_path = os.path.relpath(file_path, repo_root)

    try:
        with open(file_path, "r", errors="replace") as f:
            for line_num, line in enumerate(f, 1):
                line = line.rstrip("\n")

                # Skip empty or comment-only lines
                stripped = line.strip()
                if not stripped or stripped.startswith("#") and "=" not in stripped:
                    continue

                # Check known key patterns
                for pattern in KEY_PATTERNS:
                    if re.search(pattern["regex"], line):
                        findings.append({
                            "file": rel_path,
                            "line": line_num,
                            "name": pattern["name"],
                            "matched": line.strip()[:80],
                            "confidence": pattern["confidence"],
                            "fix": pattern["fix"],
                        })

                # Check high-entropy strings (skip known safe files)
                if not rel_path.endswith((".example", ".md", ".txt", ".lock")) and "package-lock" not in rel_path:
                    for hef in find_high_entropy_strings(line):
                        findings.append({
                            "file": rel_path,
                            "line": line_num,
                            "name": hef["name"],
                            "matched": hef["matched"],
                            "confidence": hef["confidence"],
                            "fix": hef["fix"],
                        })
    except (PermissionError, OSError):
        pass

    return findings


def scan_working_tree(repo_path: str) -> list[dict]:
    """Walk the repo and scan all text files."""
    findings = []

    for root, dirs, files in os.walk(repo_path):
        # Skip directories we should ignore
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext in SKIP_EXTENSIONS:
                continue

            full_path = os.path.join(root, fname)
            findings.extend(scan_file(full_path, repo_path))

    return findings


# ──────────────────────────────────────────────────────────────
# 7. Git history scanner (optional)
# ──────────────────────────────────────────────────────────────

def scan_git_history(repo_path: str, max_commits: int = 50) -> list[dict]:
    """Scan recent git history for secrets that were committed then removed."""
    findings = []

    try:
        result = subprocess.run(
            ["git", "log", "--all", "--diff-filter=A", f"-n{max_commits}",
             "--pretty=format:%H %s", "--name-only"],
            cwd=repo_path, capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            return findings

        current_commit = ""
        current_msg = ""
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            # Check if this line is a commit hash + message
            parts = line.split(" ", 1)
            if len(parts) == 2 and len(parts[0]) == 40 and all(c in "0123456789abcdef" for c in parts[0]):
                current_commit = parts[0][:8]
                current_msg = parts[1]
            else:
                # This is a filename - check if it's a secret file
                fname = line.strip()
                basename = os.path.basename(fname)
                for pat in SECRET_FILE_PATTERNS:
                    if pat.startswith("*."):
                        if basename.endswith(pat[1:]):
                            findings.append({
                                "file": f"{fname} (in commit {current_commit})",
                                "line": 0,
                                "name": f"Secret file in git history: {basename}",
                                "confidence": 0.85,
                                "fix": f"This file was committed in '{current_msg}'. Use 'git filter-branch' or BFG Repo Cleaner to remove it from history.",
                            })
                    elif basename == pat:
                        findings.append({
                            "file": f"{fname} (in commit {current_commit})",
                            "line": 0,
                            "name": f"Secret file in git history: {basename}",
                            "confidence": 0.90,
                            "fix": f"This file was committed in '{current_msg}'. Use 'git filter-branch' or BFG Repo Cleaner to remove it from history.",
                        })
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return findings


# ──────────────────────────────────────────────────────────────
# 8. Main CLI
# ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Key Leak Scanner - Scan a repository for leaked API keys and secrets",
        epilog="Example: python scanner.py ./sample_repo",
    )
    parser.add_argument("repo_path", help="Path to the repository to scan")
    parser.add_argument("--history", action="store_true",
                        help="Also scan git history for secrets in old commits")
    parser.add_argument("--json", action="store_true",
                        help="Output results as JSON")
    args = parser.parse_args()

    repo_path = os.path.abspath(args.repo_path)
    if not os.path.isdir(repo_path):
        print(f"Error: '{repo_path}' is not a valid directory.")
        sys.exit(1)

    print("=" * 60)
    print("  Key Leak Scanner")
    print(f"  Scanning: {repo_path}")
    print("=" * 60)

    all_findings = []

    # Check .gitignore
    print("\n  [1/3] Checking .gitignore coverage...")
    gitignore_findings = check_gitignore(repo_path)
    all_findings.extend(gitignore_findings)
    print(f"        Found {len(gitignore_findings)} issue(s)")

    # Scan working tree
    print("  [2/3] Scanning files for key patterns + entropy...")
    tree_findings = scan_working_tree(repo_path)
    all_findings.extend(tree_findings)
    print(f"        Found {len(tree_findings)} issue(s)")

    # Optionally scan git history
    if args.history:
        print("  [3/3] Scanning git history...")
        history_findings = scan_git_history(repo_path)
        all_findings.extend(history_findings)
        print(f"        Found {len(history_findings)} issue(s)")
    else:
        print("  [3/3] Git history scan skipped (use --history to enable)")

    # Output
    if args.json:
        import json
        print(json.dumps(all_findings, indent=2))
        return

    print(f"\n  SCAN RESULTS: {len(all_findings)} finding(s)")
    print(f"  {'-'*50}")

    if not all_findings:
        print("  No leaked keys or secrets detected. Repository looks clean!")
        return

    # Sort by confidence (highest first)
    all_findings.sort(key=lambda f: f["confidence"], reverse=True)

    for i, f in enumerate(all_findings, 1):
        severity = "HIGH" if f["confidence"] >= 0.85 else "MEDIUM" if f["confidence"] >= 0.60 else "LOW"
        print(f"\n  [{i}] {severity} - {f['name']}")
        print(f"      File:       {f['file']}")
        if f.get("line", 0) > 0:
            print(f"      Line:       {f['line']}")
        if f.get("matched"):
            print(f"      Match:      {f['matched']}")
        print(f"      Confidence: {f['confidence']:.0%}")
        print(f"      Fix:        {f['fix']}")

    # Summary
    high = sum(1 for f in all_findings if f["confidence"] >= 0.85)
    medium = sum(1 for f in all_findings if 0.60 <= f["confidence"] < 0.85)
    low = sum(1 for f in all_findings if f["confidence"] < 0.60)
    print(f"\n  SUMMARY: {high} HIGH | {medium} MEDIUM | {low} LOW")

    if high > 0:
        print("\n  ACTION REQUIRED: High-confidence secrets detected!")
        print("  Rotate the affected keys immediately and remove them from the repo.")


if __name__ == "__main__":
    main()
