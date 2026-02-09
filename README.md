# Smart Dealer 🏷️

**Intelligent multi-agent price comparison system** that finds the best prices and deals across food delivery, e-commerce, ride-sharing, and hotel platforms — all in one search.

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?logo=fastapi)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│                     React Frontend                         │
│          SearchBar → CategoryTabs → ResultsGrid            │
└──────────────────────────┬─────────────────────────────────┘
                           │  REST API
┌──────────────────────────▼─────────────────────────────────┐
│                    FastAPI Backend                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Orchestrator Agent                       │  │
│  │   NLP Parser → Route → Fan-out → Rank → Respond      │  │
│  └─────┬────────┬──────────┬────────┬──────────┬────────┘  │
│        │        │          │        │          │            │
│  ┌─────▼──┐ ┌──▼───┐ ┌───▼──┐ ┌──▼────┐ ┌──▼──────┐     │
│  │ Food   │ │ E-Com│ │ Ride │ │ Hotel │ │  Deal   │     │
│  │ Agent  │ │ Agent│ │Agent │ │ Agent │ │ Finder  │     │
│  └────────┘ └──────┘ └──────┘ └───────┘ └─────────┘     │
│                                                            │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────┐   │
│  │ Ranking │ │  Cache   │ │ Scraper  │ │Notifications│   │
│  │ Engine  │ │ (Redis)  │ │  Module  │ │   Service   │   │
│  └─────────┘ └──────────┘ └──────────┘ └─────────────┘   │
└────────────────────────────────────────────────────────────┘
```

## Features

- **Natural Language Search** — "Find me the cheapest pizza within 30 min"
- **6 Specialized Agents** — Food, E-Commerce, Rides, Hotels, Deals, User Profile
- **Parallel Platform Search** — All platforms queried simultaneously
- **Total Cost Transparency** — All fees, taxes, and service charges displayed
- **Smart Ranking** — Weighted algorithm (price 40%, time 20%, rating 20%, fees 10%, preferences 10%)
- **Deal Detection** — Promo codes, cashback, and seasonal offers auto-applied
- **Real-Time Results** — Sub-second response times with caching

## Platforms Covered

| Category | Platforms |
|----------|-----------|
| 🍕 Food | Uber Eats, DoorDash, Grubhub, Postmates |
| 🛒 Products | Amazon, eBay, Walmart, Target, Best Buy |
| 🚗 Rides | Uber, Lyft, Taxi |
| 🏨 Hotels | Booking.com, Expedia, Airbnb, Hotels.com, Vrbo |

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- (Optional) Docker & Docker Compose

### Option 1: Docker Compose (recommended)

```bash
# Copy env file
cp backend/.env.example backend/.env

# Start everything
docker compose up --build
```

- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:5173

### Option 2: Manual

**Backend**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
cp .env.example .env          # edit with your API keys

uvicorn app.main:app --reload
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/search/` | Full search with NLP parsing |
| `GET`  | `/api/search/quick` | Quick search via query params |
| `GET`  | `/api/deals/` | List active deals by category |
| `GET`  | `/api/profile/{id}` | Get user preferences |
| `PUT`  | `/api/profile/{id}` | Update user preferences |
| `GET`  | `/api/notifications/` | Pending notifications |
| `GET`  | `/api/health` | Health check |
| `GET`  | `/api/platforms` | Supported platforms list |

### Example Search

```bash
curl -X POST http://localhost:8000/api/search/ \
  -H "Content-Type: application/json" \
  -d '{"query": "cheapest pizza delivery within 30 minutes"}'
```

## Project Structure

```
Smart Dealer/
├── backend/
│   ├── app/
│   │   ├── agents/              # Multi-agent system
│   │   │   ├── base_agent.py    # Abstract base class
│   │   │   ├── orchestrator.py  # Central coordinator
│   │   │   ├── food_agent.py    # Food delivery comparison
│   │   │   ├── ecommerce_agent.py
│   │   │   ├── ride_agent.py    
│   │   │   ├── hotel_agent.py   
│   │   │   ├── deal_agent.py    # Promo & deal finder
│   │   │   └── user_profile_agent.py
│   │   ├── models/
│   │   │   ├── enums.py         # Platform, category enums
│   │   │   ├── schemas.py       # Pydantic request/response models
│   │   │   └── tables.py        # SQLAlchemy ORM models
│   │   ├── routes/              # FastAPI route handlers
│   │   ├── services/
│   │   │   ├── nlp_parser.py    # Natural language understanding
│   │   │   ├── ranking.py       # Weighted scoring algorithm
│   │   │   ├── cache.py         # Redis / in-memory cache
│   │   │   ├── scraper.py       # Rate-limited HTTP client
│   │   │   └── notifications.py # Alerts & events
│   │   ├── config.py
│   │   ├── database.py
│   │   └── main.py              # FastAPI app entry point
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/          # React UI components
│   │   ├── App.jsx
│   │   ├── api.js               # Axios API client
│   │   └── main.jsx
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── README.md
```

## Ranking Algorithm

Results are scored on a 0–1 scale using weighted factors:

$$\text{score} = 0.4 \times P + 0.2 \times T + 0.2 \times R + 0.1 \times F + 0.1 \times U$$

Where:
- **P** = Price score (lower is better, normalised)
- **T** = Time/delivery score (lower is better)
- **R** = Rating score (higher is better)
- **F** = Fee score (lower extra fees is better)
- **U** = User preference match

Weights are customisable per user via the Profile API.

## Extending the System

### Add a New Platform

1. Create a platform adapter function in the relevant agent file
2. Add the platform to `Platform` enum in `models/enums.py`
3. Register it in the agent's `PLATFORM_SEARCHERS` dict
4. The orchestrator and ranking engine handle the rest automatically

### Add a New Agent Category

1. Create a new agent file extending `BaseAgent`
2. Add the category to `SearchCategory` enum
3. Register in `OrchestratorAgent._category_agent_map`

## License

MIT
