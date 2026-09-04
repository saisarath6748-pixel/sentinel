# 🛡️ Abuse-Ring Sentinel

> **Razorpay Buildathon — Track 02: AI Risk Manager**

Abuse-Ring Sentinel is an enterprise-grade AI risk management system designed to detect and mitigate coordinated buyer-side abuse rings (e.g., promo farming, refund abuse, and return fraud) across Razorpay merchants.

Built for precision and scale, Sentinel acts as an intelligent watchdog. It identifies malicious patterns and flags suspicious clusters for human review without aggressively auto-banning legitimate customers.

---

## 🚀 About Sentinel

Built for the **Razorpay /buildathon 2026**, **Sentinel** is an enterprise AI risk management platform designed to secure digital merchants across three vital dimensions:

### 1. Real-Time Abuse Ring Detector
As fraud techniques evolve from isolated bad actors into organized network attacks, traditional rule-based filters fail. Sentinel uses multi-dimensional signal extraction and deterministic graph clustering to expose hidden links between seemingly disconnected buyer accounts. It proactively isolates and flags coordinated abuse rings (e.g., promo farming, refund syndicates, and return fraud) before they can impact your bottom line.

### 2. Live Payments & Real-Time Razorpay Ingestion
Sentinel connects directly to the **Razorpay Payments API** to ingest live test-mode transactions in real time. Transactions are continuously enriched with card/VPA fingerprinting and cross-referenced against active abuse clusters, enabling risk teams to monitor payment flow health, catch card-testing spikes, and trace payments back to active syndicates with one click.

### 3. API Key Leak Scanner
Security starts at the source. Taking direct reference from Razorpay's documented **Payouts Best Practices** and developer integration guidelines, leaving private API keys in client-side code or public version control is a major security vulnerability. Sentinel features a standalone scanner that audits frontends, build artifacts, git commit history, and `.gitignore` hygiene for exposed Razorpay Live and Test keys (`rzp_live_*`, `rzp_test_*`), keeping credentials secure before deployment.

> **Important Note for the Buildathon:** The frontend dashboard provided in this repository serves as a visual control center demonstrating the capabilities of Sentinel. In production, the **Abuse Ring Detector**, **Live Ingestion Engine**, and **API Key Leak Scanner** are modular services engineered to integrate into existing merchant checkout pipelines, risk orchestration platforms, or CI/CD workflows.

## 🕵️‍♂️ How it Detects Abuse Rings

Sentinel's detection engine operates in three core phases:

1. **Signal Extraction**: Extracts shared entities across accounts such as Device IDs, IP Addresses, Shipping/Billing Addresses, Card Fingerprints (BIN/IIN, card network, issuing bank, last 4 digits), and transaction timing patterns.
2. **Deterministic Clustering**: Models these signals as an entity graph to deterministically cluster accounts that share a suspiciously high overlap of identifiable markers.
3. **LLM-Powered Contextualization & Scoring**: Leverages Large Language Models to evaluate clustered network topologies, generating a risk score and an interpretable narrative of *why* the syndicate was flagged, giving fraud analysts instant context.

## 💳 Live Payments & Real-Time Razorpay Ingestion

Accessible via the **Live Payments** tab (`/payments`), this module provides real-time visibility into incoming payments directly from the Razorpay API and correlates them with Sentinel's risk detection engine:

1. **Direct Razorpay Test-Mode Sync**: Connects natively to Razorpay via your test credentials (`RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`). With the **"Sync Razorpay"** action (`POST /razorpay/ingest`), new payments are fetched instantly and incorporated into Sentinel's data pipeline.
2. **Dynamic Abuse Ring Cross-Referencing**: Every transaction is cross-referenced in real time against active graph clusters. If a payment originates from an account belonging to a flagged syndicate, it is badged with a high-visibility, pulsing **"Ring Flagged"** indicator along with its specific cluster ID.
3. **One-Click Deep-Link Investigation**: Clicking any **"Ring Flagged"** badge instantly navigates the analyst to the Ring Detector view (`/`), isolating the corresponding syndicate graph and displaying the full LLM forensic explanation.
4. **Card & Payment Fingerprinting**: Enriches raw payment data by extracting card BINs, card issuers (e.g., HDFC, ICICI, SBI), network brands (Visa, Mastercard, RuPay), tokenized card identifiers, and UPI VPAs without storing unmasked sensitive payment data.
5. **Operational Health & Filtering**:
   - **Real-Time KPIs**: Track Total Ingested Payments, Captured Volume (₹ INR), Failed Authorization Attempts (highlighting rapid card testing or velocity abuse), and Ring-Flagged transaction counts.
   - **Instant Search**: Search transactions on the fly by Payment ID (`pay_*`), customer email address, or contact number.
   - **Status Tabs**: Filter between **All**, **Captured**, **Failed**, and **Abuse Rings** to rapidly triage payment anomalies.

## 🔑 How the API Key Leak Scanner Works

Formulated with reference to Razorpay's **Major Security Risks** and **Common Problems** developer documentation, this standalone module addresses the widespread industry issue of merchants leaving private API keys in client-facing frontend assets or committing them to repositories:

1. **Frontend & Codebase Inspection**: Scans client-side JavaScript/TypeScript files, frontend build artifacts, and project directories to ensure private merchant API keys are never bundled into customer-facing applications.
2. **Repository & Git History Auditing**: Analyzes working directories as well as historical git commits using regex signature matching and Shannon entropy to catch hardcoded Razorpay Live/Test credentials (`rzp_live_*`, `rzp_test_*`) and service tokens.
3. **Hygiene & Actionable Remediation**: Verifies `.gitignore` configurations against common secret patterns (e.g., `.env`, `.env.local`) and generates clear, actionable remediation guidance, including key rotation protocols and secure environment variable workflows.

## 🏗️ Architecture

Sentinel is built using a modern, decoupled architecture designed for rapid iteration and scalability:

- **Frontend (Dashboard)**: Next.js (React), Tailwind CSS, and Lucide icons featuring the **Ring Detector** (`/`), **Live Payments Monitor** (`/payments`), and **Key Leak Scanner** (`/key-scanner`).
- **Backend API**: Python (FastAPI) providing high-throughput endpoints for cluster detection, Razorpay synchronization (`/razorpay/payments`, `/razorpay/ingest`), authentication, and key auditing.
- **Data Pipeline**: Python-based ingestion, normalization, and synthetic data generation scripts.
- **Detection & AI Engine**: Network graph clustering algorithms coupled with LLM inference (via Groq / OpenAI) for semantic risk analysis.
- **Database**: Local SQLite with bcrypt authentication and Supabase / PostgreSQL schema support.

### Directory Structure

```text
sentinel/
├── api/             # FastAPI routes (clustering, auth, /razorpay/payments, /razorpay/ingest)
├── dashboard/       # Next.js frontend (Ring Detector, Live Payments, Key Scanner)
│   └── src/app/
│       ├── page.tsx          # Ring Detector & visual cluster explanation
│       ├── payments/page.tsx # Live Payments monitor & Razorpay sync
│       └── key-scanner/      # Leaked API key detection & remediation
├── data/            # Synthetic transaction data and payment metadata storage
├── db/              # Database schema, migrations, and merchant seed scripts
├── detection/       # Core clustering and signal extraction algorithms
├── eval/            # Evaluation scripts for detection accuracy
├── ingestion/       # Razorpay client (test-mode payment pull) & normalization
├── key-scanner/     # Standalone scanner detecting leaked API keys in frontends & git repos
├── llm/             # LLM prompt engineering and cluster narrative explanations
└── scripts/         # Utility scripts (test data generation, environment setup)
```

## 🔐 Demo Accounts

To explore the dashboard, log in with any of the following pre-configured demo merchant accounts:

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
*Open `.env` and configure your credentials:*
- `GROQ_API_KEY`: Required for LLM-powered ring explanations (free at console.groq.com).
- `RAZORPAY_KEY_ID` & `RAZORPAY_KEY_SECRET`: *(Optional)* Your Razorpay test-mode API keys to enable live payment ingestion for Gamma Groceries.

### 3. Install Dependencies

Install both the backend Python packages and the frontend Node.js dependencies using the setup script:
```bash
npm run setup
```

### 4. Database Setup

The database initializes and seeds the demo accounts automatically upon API startup. If you wish to provision external Supabase tables, execute `db/schema.sql` in your Supabase SQL Editor.

### 5. Generate Synthetic Data & Run Detection

> **Note:** The Alpha and Beta demo accounts come with detections already pre-calculated on synthetic data for instant exploration. The **Gamma Groceries** account is connected directly to Razorpay test mode; when you navigate to the **Live Payments** page and click **"Sync Razorpay"**, real test payments are ingested and dynamically evaluated against the clustering engine.

To generate new synthetic abuse data and run the evaluation pipeline locally:

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
- Sign in as **Gamma Groceries** (`merchant_gamma@demo.sentinel` / `password123`) to view and sync **Live Payments**.
- Sign in as **Alpha Electronics** or **Beta Fashion** to explore pre-calculated cross-merchant abuse rings.
