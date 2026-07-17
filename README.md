# Panen Pay

Panen Pay is the cooperative's **evidence layer** at the chili intake desk. The
operator photographs the harvest (an LLM grades it into `fresh` / `sell_today` /
`wilted`), the batch sits on an ESP32 load-cell scale streaming live weight, a
deterministic engine prices it, and the station issues a GPS-timestamped,
SHA-256-hashed QR certificate plus a simulated payment record. Disputed grades,
disputed weights, and missing records stop costing farmers money — and the
certificate trail becomes alternative data for MSME credit. Positioning:
infrastructure for the existing cooperative channel, not a middleman
replacement.

## Architecture

```
 ESP32 station ──POST /ingest/weight──┐            ┌── (station) intake UI
 (HX711 scale + buzzer)               │            │   photo → grade → weigh → certify
   ▲ polls /station/feedback          ▼            ▼
   │                          FastAPI backend ◄──────── Next.js frontend
 scripts/simulate_station.py    /api/v1/*                (dashboard) live feed
 (drop-in hardware replacement)   │                      cert/[id] QR verification
                                  │
              ┌───────────────────┼──────────────────────┐
              ▼                   ▼                      ▼
       pricing_engine.py    vision_grader        Store adapter
       (ALL numbers,        GPT-4o strict enum   Firestore ⇄ InMemory
        pure + tested)      ⇄ deterministic mock (selected by env)
              │
       certificate_svc.py ── canonical JSON → SHA-256 → QR
       mock_ledger.py ────── status: "paid_mock" (R3: simulated only)
```

## Quickstart (zero credentials — the default)

```bash
# 1. backend (keyless: mock grader + in-memory store)
cd backend
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt
.venv/Scripts/python -m uvicorn app.main:app --port 8000
# GET http://localhost:8000/healthz → {"ok":true,"grader":"mock","store":"memory"}

# 2. frontend (poll mode)
cd frontend && npm install && npm run dev   # http://localhost:3000

# 3. drive a demo without hardware
python scripts/simulate_station.py --scenario happy   # or: rush
```

Tests and evals:

```bash
cd backend && .venv/Scripts/python -m pytest -q
.venv/Scripts/python evals/run_eval.py --mock          # keyless harness check
```

## Environment (§E degradation matrix)

Copy `.env.example` → `.env`. Every feature works with every variable empty.

| Variable | Present | Absent (default) |
|---|---|---|
| `OPENAI_API_KEY` | GPT-4o vision grading + Bahasa briefs | Deterministic mock grader + template briefs |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Firestore store | In-memory store |
| `PANEN_BASE_URL` | QR payload origin | `http://localhost:8000` |
| `NEXT_PUBLIC_API_BASE` | Frontend → backend base | `http://localhost:8000` |
| `NEXT_PUBLIC_DATA_MODE` | `firestore` → onSnapshot live feed | `poll` → 2s SWR polling |

## AI-usage disclosure

| Component | AI involvement |
|---|---|
| Photo grading | GPT-4o, temperature 0, strict enum schema (`fresh/sell_today/wilted`); off-schema output rejected, never coerced |
| Transaction briefs | GPT-4o restates engine numbers only; any digit not present in the input payload is rejected → template fallback |
| **All prices, totals, weights** | **Deterministic `pricing_engine.py` — the LLM never generates a number (R1)** |
| Payments | None — simulated (`paid_mock`), badged on every surface (R3) |
| Codebase | Built with AI assistance (Claude Code) against a human-written spec; pricing, hashing, and API behavior are unit/integration tested |

## Photos

All 4 image slots currently ship as generated gray placeholders. Real photos
enter `frontend/public/images/` only after an attribution row exists in
[docs/ASSETS.md](docs/ASSETS.md) (Unsplash/Pexels only).

## Tech stack

FastAPI · Pydantic v2 · Uvicorn · OpenAI SDK (GPT-4o, Structured Outputs) ·
firebase-admin (optional) · qrcode + Pillow · pytest — Next.js 16 (App Router,
Turbopack) · React 19 · Tailwind v4 · SWR · firebase web SDK (optional) —
ESP32 + HX711 + ArduinoJson — simulator: httpx + stdlib.

## Docs

[PITCH.md](docs/PITCH.md) · [DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) ·
[JUDGES.md](docs/JUDGES.md) · [VIDEO_SHOTLIST.md](docs/VIDEO_SHOTLIST.md) ·
[ASSETS.md](docs/ASSETS.md)
