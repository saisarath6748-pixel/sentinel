# 🛡️ Abuse-Ring Sentinel

> **Razorpay Buildathon — Track 02: AI Risk Manager**

Abuse-Ring Sentinel is an enterprise-grade AI risk management system designed to detect and mitigate coordinated buyer-side abuse rings (e.g., promo farming, refund abuse, and return fraud) across Razorpay merchants.

Built for precision and scale, Sentinel acts as an intelligent watchdog. It identifies malicious patterns and flags suspicious clusters for human review without aggressively auto-banning legitimate customers.

---

## 🚀 About Sentinel

Built for the **Razorpay /buildathon 2026**, **Sentinel** is a dual-engine AI risk management platform designed to secure your business on two critical fronts:

### 1. Real-Time Abuse Ring Detector
As fraud techniques evolve into coordinated network attacks, traditional rule-based systems fall short. Sentinel leverages multi-dimensional signal extraction and deterministic graph clustering to uncover hidden connections between seemingly unrelated accounts. It proactively identifies and blocks coordinated abuse rings (e.g., promo farming, return fraud) before they can impact your bottom line.

### 2. API Key Leak Scanner
Security starts at the source. A pervasive vulnerability identified across merchant integrations is the accidental exposure of API credentials—specifically when developers unintentionally leave active API keys embedded in frontend client-side scripts, application bundles, or version control repositories.

Taking direct reference from Razorpay's documented **Payouts Best Practices** and integration guidelines, leaving API keys exposed in frontend code or pushed to repositories represents a critical security risk that can lead to credential theft, unauthorized API access, and transaction manipulation. Sentinel incorporates a dedicated, standalone credential scanner to address this major issue proactively. It audits merchant codebases, frontend files, git commit histories, and `.gitignore` configurations for leaked Razorpay Live and Test keys (`rzp_live_*`, `rzp_test_*`), intercepting exposures before code goes live to ensure integrations remain airtight.

> **Important Note for the Buildathon:** The frontend dashboard provided in this repository serves purely as a visual showcase. It is designed to demonstrate the capabilities and outputs of the Sentinel platform in a digestible format for the buildathon. However, the **Abuse Ring Detector** and **API Key Leak Scanner** are fundamentally independent, modular tools. In a real-world production environment, these backend modules are intended to be integrated directly into a merchant's existing infrastructure, risk engines, or CI/CD pipelines as standalone services.

## 🕵️‍♂️ How it Detects Abuse Rings

Sentinel's detection engine works in three core phases:

1. **Signal Extraction**: Extracts shared entities across accounts such as Device IDs, IP Addresses, Shipping/Billing Addresses, Card Fingerprints, and transaction timings.
2. **Deterministic Clustering**: Models these signals as a graph to deterministically cluster accounts that share a suspiciously high overlap of identifiable markers.
3. **LLM-Powered Contextualization & Scoring**: Leverages Large Language Models to evaluate clustered data, providing a risk score and a human-readable explanation of *why* the cluster is flagged, ensuring your risk teams can make swift, informed decisions.

## 🔑 How the API Key Leak Scanner Works

Formulated with reference to Razorpay's **Major Security Risks** and **Common Problems** developer documentation, this standalone module addresses the widespread industry issue of merchants leaving private API keys in client-facing frontend assets or committing them to repositories:

1. **Frontend & Codebase Inspection**: Scans client-side JavaScript/TypeScript files, frontend build artifacts, and project directories to ensure private merchant API keys are never bundled into customer-facing applications.
2. **Repository & Git History Auditing**: Analyzes working directories as well as historical git commits using regex signature matching and Shannon entropy to catch hardcoded Razorpay Live/Test credentials (`rzp_live_*`, `rzp_test_*`) and service tokens.
3. **Hygiene & Actionable Remediation**: Verifies `.gitignore` configurations against common secret patterns (e.g., `.env`, `.env.local`) and generates clear, actionable remediation guidance, including key rotation protocols and secure environment variable workflows.

## 🏗️ Architecture

Sentinel is built using a modern, decoupled architecture designed for rapid iteration and scalability:

- **Frontend (Dashboard)**: Next.js (React), Tailwind CSS, and shadcn/ui for a highly responsive, modern risk management interface.
- **Backend API**: Python (FastAPI/Flask) for high-throughput, low-latency API endpoints serving the dashboard.
- **Data Pipeline**: Python-based ingestion, normalization, and synthetic data generation scripts.
- **Detection & AI Engine**: Network graph clustering algorithms coupled with LLM inference (GPT models) for semantic risk analysis.
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
├── key-scanner/     # Standalone scanner detecting leaked API keys in merchant frontends & repos
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

> **Note:** The synthetic data generation is strictly for testing purposes. The Alpha and Beta demo accounts come with detections already pre-calculated on this synthetic data for easy exploration. On the other hand, real Razorpay test-mode payments are synced using the syncing function, and the "Gamma Groceries" demo merchant showcases the detection of these real-time test payments in action.

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

Visit `http://localhost:3003` to access the Sentinel Dashboard.
