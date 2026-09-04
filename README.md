# Abuse-Ring Sentinel

**Razorpay Buildathon — Track 02: AI Risk Manager**

Abuse-Ring Sentinel detects coordinated buyer-side abuse rings (promo farming,
refund abuse, return fraud) across Razorpay merchants. It works by extracting
shared signals (device, address, card, timing) across accounts, clustering
them deterministically, and surfacing flagged clusters for human review — never
auto-banning.

A bundled **API Key Leak Scanner** checks codebases for exposed Razorpay/API
secrets before merchants go live.

## Demo Accounts

You can log in to the dashboard using any of the following demo credentials (password: `password123`):
- `merchant_alpha@demo.sentinel`
- `merchant_beta@demo.sentinel`
- `merchant_gamma@demo.sentinel`

## Quick Start

```bash
cp .env.example .env        # fill in real keys
pip install -r requirements.txt

# Step 0: run schema.sql in Supabase SQL Editor, then:
python db/seed_demo_merchants.py

# Step 1: generate synthetic data
python data/generate_synthetic.py

# Step 2-3: detect + evaluate
python eval/evaluate.py
```

See `PROJECT_BRIEF.md` for full architecture and build order.
