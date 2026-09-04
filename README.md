# 🛡️ Abuse-Ring Sentinel

> **Razorpay Buildathon — Track 02: AI Risk Manager**

Abuse-Ring Sentinel is an enterprise-grade AI risk management system designed to detect and mitigate coordinated buyer-side abuse rings (e.g., promo farming, refund abuse, and return fraud) across Razorpay merchants.

Built for precision and scale, Sentinel acts as an intelligent watchdog. It identifies malicious patterns and flags suspicious clusters for human review without aggressively auto-banning legitimate customers.

---

## 🚀 About Sentinel

As fraud techniques evolve into coordinated network attacks, traditional rule-based systems fall short. Sentinel leverages multi-dimensional signal extraction and deterministic clustering to uncover hidden connections between seemingly unrelated accounts. 

Additionally, Sentinel ships with a bundled **API Key Leak Scanner** to proactively check merchant codebases for exposed Razorpay/API secrets before they go live, addressing both transactional risk and infrastructure security.

## 🕵️‍♂️ How it Detects Abuse Rings

Sentinel's detection engine works in three core phases:

1. **Signal Extraction**: Extracts shared entities across accounts such as Device IDs, IP Addresses, Shipping/Billing Addresses, Card Fingerprints, and transaction timings.
2. **Deterministic Clustering**: Models these signals as a graph to deterministically cluster accounts that share a suspiciously high overlap of identifiable markers.
3. **LLM-Powered Contextualization & Scoring**: Leverages Large Language Models to evaluate clustered data, providing a risk score and a human-readable explanation of *why* the cluster is flagged, ensuring your risk teams can make swift, informed decisions.

## 🏗️ Architecture

Sentinel is built using a modern, decoupled architecture designed for rapid iteration and scalability:

- **Frontend (Dashboard)**: Next.js (React), Tailwind CSS, and shadcn/ui for a highly responsive, modern risk management interface.
- **Backend API**: Python (FastAPI/Flask) for high-throughput, low-latency API endpoints serving the dashboard.
- **Data Pipeline**: Python-based ingestion, normalization, and synthetic data generation scripts.
- **Detection & AI Engine**: Network graph clustering algorithms coupled with LLM inference (`llama_client.py`) for semantic risk analysis.
- **Database**: Supabase / PostgreSQL for robust, relational data storage.

### Directory Structure

```text
sentinel/
├── api/             # Backend API routes and main application logic
├── dashboard/       # Next.js frontend dashboard
├── data/            # Synthetic data generation and raw data storage
├── db/              # Database schemas and seeding scripts
├── detection/       # Core clustering and signal extraction algorithms
├── eval/            # Evaluation scripts for detection accuracy
├── ingestion/       # Razorpay client and data normalization logic
├── key-scanner/     # Bundled API key leak scanner for merchant codebases
├── llm/             # LLM client and prompt engineering for cluster explanations
└── scripts/         # Utility scripts (test data generation, environment setup)
```

## 🔐 Demo Accounts

To explore the dashboard as a merchant, use any of the following demo credentials.

**Password for all demo accounts:** `password123`

- 🏢 `merchant_alpha@demo.sentinel`
- 🏢 `merchant_beta@demo.sentinel`
- 🏢 `merchant_gamma@demo.sentinel`

## ⚡ Quick Setup

Follow these steps to clone the repository, set up your environment, and spin up the Sentinel platform locally.

### 1. Clone the Repository

```bash
git clone https://github.com/saisarath6748-pixel/sentinel.git
cd sentinel
```

### 2. Environment Configuration

```bash
cp .env.example .env
```
*Open the `.env` file and populate it with your Supabase credentials and LLM API keys.*

### 3. Install Dependencies

Install both the backend Python packages and the frontend Node.js dependencies using the setup script:
```bash
npm run setup
```

### 4. Database Setup

1. Run the SQL commands found in `db/schema.sql` within your Supabase SQL Editor to provision the tables.
2. Seed the database with demo merchants:
```bash
python db/seed_demo_merchants.py
```

### 5. Generate Synthetic Data & Run Detection

> **Note:** The synthetic data generation is strictly for testing purposes. Real Razorpay test-mode payments are synced using the syncing function, and the "Gamma Groceries" demo merchant showcases the detection of these test payments in action.

To test the system locally, you can generate synthetic abuse data and run the evaluation pipeline:

```bash
# Generate synthetic transactional data
python data/generate_synthetic.py

# Run the detection algorithms and evaluate
python eval/evaluate.py
```

### 6. Run the Application

Start both the backend API and frontend dashboard concurrently:

```bash
npm start
```

Visit `http://localhost:3000` to access the Sentinel Dashboard.
