# Stocker 📈
AI Multi-Agent Investment Research Platform for NSE/BSE stocks.

Multiple specialized AI agents independently analyze stocks from different angles — technical, sentiment, and fundamental — then a local LLM (Ollama) aggregates their findings into a BUY / SELL / HOLD recommendation.

**Total cost to run: ₹0**

---

## Tech Stack
- **Backend:** Python, FastAPI, SQLAlchemy, SQLite
- **Agents:** pandas-ta, VADER (nltk), yfinance, feedparser
- **LLM:** Ollama (llama3:8b, runs locally)
- **Frontend:** React + Vite, Recharts, TanStack Query
- **Scheduler:** APScheduler

---

## Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+
- Ollama installed — https://ollama.com

### 1. Clone the repo
```bash
git clone https://github.com/RishitMahapatra/Stocker.git
cd Stocker
```

### 2. Python environment
```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows

pip install -r requirements.txt
python -m nltk.downloader vader_lexicon
```

### 3. Environment variables
```bash
cp .env.example .env
# Edit .env if needed (defaults work for local dev)
```

### 4. Ollama setup
```bash
ollama pull llama3
ollama serve
# Verify:
ollama run llama3 "respond with: ok"
```

### 5. Frontend setup
```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:5173
```

### 6. Start the backend
```bash
# From Stocker root
uvicorn backend.main:app --reload --host localhost --port 8000
```

---

## Project Structure
```
Stocker/
├── backend/
│   ├── agents/          # Technical, Sentiment, Fundamental, Decision, Risk
│   ├── api/             # FastAPI route handlers
│   ├── data/            # Fetchers, feature engineering, validators
│   ├── paper_trading/   # Paper trade engine and portfolio
│   ├── schemas/         # Pydantic models
│   ├── monitoring/      # Logging and metrics
│   └── tests/           # All test files
├── frontend/            # React + Vite dashboard
├── data/                # SQLite database (gitignored)
├── logs/                # Pipeline logs (gitignored)
├── ollama/              # Ollama setup notes
├── .env.example         # Environment variable template
├── requirements.txt     # Python dependencies
└── README.md
```

---

## Build Phases
| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Environment & Scaffolding | ✅ |
| 1 | Data Ingestion | 🔲 |
| 2 | Technical Agent | 🔲 |
| 3 | Sentiment Agent | 🔲 |
| 4 | Fundamental Agent | 🔲 |
| 5 | Decision + Risk Engine | 🔲 |
| 6 | FastAPI + Scheduler | 🔲 |
| 7 | Paper Trading Engine | 🔲 |
| 8 | React Dashboard | 🔲 |
| 9 | Hardening & MVP Complete | 🔲 |

---

## Important
- Never commit `.env` or `data/*.db` — both are gitignored
- Ollama runs locally — no cloud LLM calls in MVP
- Paper trading runs for 30 days before any live broker integration
