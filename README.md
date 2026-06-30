# Stocker

<p align="center">
  <img width="1983" height="793" alt="thumbnail" src="https://github.com/user-attachments/assets/069edbe7-d52c-487c-9d87-30728f3bef66" />
</p>

<h1 align="center"> STOCKER </h1>

<p align="center">
<b>AI Multi-Agent Investment Research Platform for NSE & BSE Stocks</b>
</p>

<p align="center">
Technical Analysis • Sentiment Analysis • Fundamental Analysis • Local LLM Decision Engine
</p>

<p align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge\&logo=python\&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge\&logo=fastapi\&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge\&logo=react)
![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-black?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

</p>

---

# What is Stocker?

Stocker is an **AI-powered investment research platform** built specifically for **Indian stock markets (NSE/BSE)**.

Instead of relying on a single AI prompt, Stocker employs **multiple specialized AI agents** that independently analyze a stock from different perspectives.

Each agent produces its own report before a **locally running LLM (Ollama)** aggregates every finding into a final:

* 🟢 BUY
* 🟡 HOLD
* 🔴 SELL

recommendation.

Everything runs **locally**.

**No paid APIs. No OpenAI credits. No cloud inference.**

> **Total inference cost:** **₹0**

---

# Architecture

```text
                    Market Data
                         │
        ┌────────────────┴────────────────┐
        │                                 │
 Technical Agent                 Sentiment Agent
        │                                 │
        └──────────────┬──────────────────┘
                       │
              Fundamental Agent
                       │
              Risk Assessment Agent
                       │
                Ollama (Llama3)
                       │
         BUY / HOLD / SELL Recommendation
                       │
             React Dashboard + Reports
```

---

# Features

## Technical Analysis

* RSI
* MACD
* Bollinger Bands
* EMA
* SMA
* Trend Detection
* Volume Analysis

---

## Sentiment Analysis

* Google News
* RSS Feeds
* Financial Headlines
* VADER Sentiment
* Confidence Score

---

## Fundamental Analysis

* Revenue
* EPS
* PE Ratio
* Market Cap
* ROE
* Debt Metrics

---

## AI Decision Engine

Instead of asking one model one question...

Stocker asks **multiple independent agents**.

The local LLM then:

* Reads every report
* Detects conflicts
* Weighs confidence
* Produces reasoning
* Gives the final recommendation

---

# Why Stocker?

Unlike most stock assistants that depend entirely on ChatGPT or paid APIs...

Stocker is designed to be

* ✅ Completely Local
* ✅ Privacy Friendly
* ✅ Zero API Cost
* ✅ Modular
* ✅ Explainable
* ✅ Easy to Extend

---

# Tech Stack

| Category   | Technologies                                  |
| ---------- | --------------------------------------------- |
| Backend    | FastAPI, Python, SQLAlchemy                   |
| Database   | SQLite                                        |
| Frontend   | React, Vite, TanStack Query                   |
| Charts     | Recharts                                      |
| AI Agents  | pandas-ta, yfinance, feedparser, nltk (VADER) |
| LLM        | Ollama (Llama 3)                              |
| Scheduling | APScheduler                                   |

---

# Getting Started

## Prerequisites

* Python 3.11+
* Node.js 18+
* Ollama

---

## Clone Repository

```bash
git clone https://github.com/RishitMahapatra/Stocker.git

cd Stocker
```

---

## Backend Setup

Create a virtual environment

```bash
python -m venv venv
```

Activate it

Mac/Linux

```bash
source venv/bin/activate
```

Windows

```powershell
venv\Scripts\activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Download VADER

```bash
python -m nltk.downloader vader_lexicon
```

---

## Environment Variables

```bash
cp .env.example .env
```

Defaults work for local development.

---

## Ollama

Install Ollama

https://ollama.com

Pull Llama 3

```bash
ollama pull llama3
```

Start Ollama

```bash
ollama serve
```

Verify

```bash
ollama run llama3 "respond with ok"
```

---

## Frontend

```bash
cd frontend

npm install

npm run dev
```

Frontend runs at

```
http://localhost:5173
```

---

## Backend

```bash
uvicorn backend.main:app --reload --host localhost --port 8000
```

Backend runs at

```
http://localhost:8000
```

---

# Project Structure

```text
Stocker
│
├── backend
│   ├── agents
│   ├── api
│   ├── data
│   ├── monitoring
│   ├── paper_trading
│   ├── schemas
│   └── tests
│
├── frontend
│
├── data
│
├── logs
│
├── ollama
│
├── requirements.txt
│
├── .env.example
│
└── README.md
```


---

# Design Philosophy

Stocker follows a **Multi-Agent AI Architecture**.

Instead of depending on one giant prompt, every component is responsible for one task.

Each agent remains:

* Independent
* Explainable
* Replaceable
* Testable

This makes the system significantly easier to improve over time.

---

# Future Roadmap

* Portfolio Tracking
* Watchlists
* Live Broker Integration
* Portfolio Optimization
* Risk Scoring
* Email Reports
* Telegram Alerts
* AI Portfolio Manager
* Backtesting Engine
* Strategy Marketplace

---

# Security

* `.env` is ignored
* SQLite database is ignored
* Logs are ignored
* No cloud LLM calls
* Local inference only

---




