# Panen Pay — agent instructions

Chili intake **evidence layer** for a cooperative: operator photographs the harvest (LLM grades it) → ESP32 load-cell scale streams weight → deterministic engine prices it → station issues a SHA-256-hashed, GPS-timestamped QR certificate + simulated payment.

Say **"evidence layer"**, never "middleman killer" or "tengkulak replacement".

Full commit-by-commit path: `docs/BUILD_PATH.md`. This file is the rules.

---

## §R Hard rules — never violate, these outrank every convenience

- **R1. The LLM never generates numbers.** Prices, totals, weights, multipliers come only from `backend/app/services/pricing_engine.py` (pure, deterministic, unit-tested). GPT-4o may only: (a) grade a photo into a fixed enum, (b) write prose that restates numbers it was given. Any LLM output containing a digit not present in its input payload is rejected.
- **R2. Clients never write to the database.** Only the FastAPI backend writes, via `store.py`. The frontend is read-only — no Firestore writes, ever. Certificate validity is decided **server-side**, never in the browser.
- **R3. Every payment surface renders `<SimulatedBadge />`.** All payments are `status: "paid_mock"`. No screen may imply real money moved.
- **R4. One commodity: chili. Three grades: `fresh` | `sell_today` | `wilted`.** No multi-crop code paths, no fourth grade.
- **R5. Secrets never enter git.** `.env*` and `serviceAccount*.json` are gitignored from commit 1. The Firebase **web** config is public by design and lives in code; the service-account JSON and `OPENAI_API_KEY` never do.
- **R6. Grading is temperature 0 with a strict enum schema.** Off-enum or malformed output → retry identical request (max 2) → HTTP 502. **Never coerce, never guess a grade.**
- **R7. Everything works with no hardware and no credentials.** Mock adapters replace OpenAI/Firestore when keys are absent; `scripts/simulate_station.py` replaces the ESP32. A feature that only works with hardware plugged in or a key present is **not done**.

---

## File ownership — do not edit files outside the current member's lane

| Member | Owns |
|---|---|
| **Bani** | all `frontend/` · `services/vision_grader.py` · `services/brief_writer.py` · `routers/grade.py` · `evals/` · `tests/test_grading_schema.py` · `scripts/simulate_station.py` · `firmware/` |
| **Backend** | `app/main.py` `config.py` `deps.py` `store.py` · `models/` · `services/{pricing_engine,certificate_svc,mock_ledger}.py` · `routers/{ingest,station,transactions,certificates,health}.py` · all other `tests/` |
| **Support** | `docs/` · `README.md` · `.gitignore` · `.env.example` · `evals/golden_set/expected_grades.json` |

**Two rules that prevent almost all merge conflicts:**
1. **Only the backend dev edits `app/main.py`.** Need a router mounted? Ask them — don't edit it.
2. **Only Bani edits `frontend/src/lib/strings.ts`.** Support drafts Bahasa copy in chat; Bani pastes it.

If a task requires touching a file outside your lane, **stop and say so** instead of editing it.

---

## API contract — locked at H2, do not change

```
POST /api/v1/ingest/weight   {station_id, weight_grams, stable}
POST /api/v1/grade           multipart "photo" → GradeResult
POST /api/v1/transactions    {farmerName, gps, stationId?} → {transaction, certificate, brief}
GET  /api/v1/transactions/recent → {transactions: [...25]}
GET  /api/v1/certificates/{certId}?verify=1 → {certificate, transaction, valid}
GET  /api/v1/station/feedback?station_id= → {tone}   # READ-ONCE: clears on read
GET  /api/v1/station/state   → {state}
GET  /healthz                → {ok, grader: "mock"|"openai", store: "memory"|"firestore"}
GET  /cert/{certId}          → 307 → frontend cert page
```

Data shapes (camelCase **on purpose** — these dicts go to the JS frontend unmodified; the scale's wire payload is snake_case):
```
Tier         = "fresh" | "sell_today" | "wilted"
GradeResult  = { grade: Tier, confidence: "high"|"medium"|"low", visual_evidence: string }
Transaction  = { txId, farmerName, tier, weightKg, pricePerKg, totalIdr, gps{lat,lng},
                 createdAt, certificateHash, certId, status: "paid_mock", paidAt }
Certificate  = { certId, txId, sha256, qrPayloadUrl, issuedAt, qrPngDataUri }
StationState = { stationId, lastWeightGrams, stable, lastTier, pendingGrade, updatedAt }
```

---

## Conventions

- **Strings:** every user-facing string lives in `frontend/src/lib/strings.ts` as `{ id, en }`. **No hardcoded UI text anywhere else.** Station/cert render `.id` big + `.en` as a small subtitle; dashboard is English-only but still sourced from `strings.ts`.
- **Design tokens (locked):** canvas `#FAFBF0` · leaf `#3F7D3A` (primary, fresh) · gold `#E9B62C` (sell_today) · terra `#C0653F` (wilted) · slate `#5B6B7A` (SimulatedBadge). Font: Plus Jakarta Sans via `next/font/google`.
- **Adapters** are chosen once in `config.py` and injected via `deps.py`. Routers must never know which implementation they got.
- **Touch targets:** station buttons `min-h-20` — the operator wears gloves.
- **Commits:** conventional prefixes (`feat:` `fix:` `chore:` `docs:` `test:`). Small and frequent, on your own branch. Merges to `main` are the backend dev's.
- Prefer boring, well-documented libraries. No experimental packages.

---

## Stack gotchas — this is NOT the framework version in your training data

- **Next.js 16:** dynamic route `params` is a **`Promise`** — `const { id } = await params`. Route groups `(station)`/`(dashboard)` don't appear in URLs.
- **Tailwind v4:** there is **no `tailwind.config.ts`**. The `@theme` block in `globals.css` *is* the config; `--color-leaf` is what generates `bg-leaf`.
- **`next/image` cannot optimize `blob:` or `data:` URIs** — use plain `<img>` for camera thumbnails and the QR data-URI.
- **SWR pauses polling in hidden tabs** → always pass `refreshWhenHidden: true` for the weight and dashboard polls.
- **Firebase web SDK:** never import `getAnalytics` (touches `window` → breaks SSR). Guard init with `getApps()[0] ?? initializeApp(...)`.
- **Python money math:** `Decimal(str(x))` never `Decimal(float)`; `ROUND_HALF_UP` never the default banker's rounding; never builtin `round()`.
- **Mock determinism:** `hashlib.sha256`, never builtin `hash()` (salted per process).
- **Certificate hashing:** fields attached *after* hashing (`certificateHash`, `certId`) **must** be in `_HASH_EXCLUDED_FIELDS`, or verification fails. Canonical JSON = `sort_keys=True, separators=(",", ":")` — **frozen forever**; changing it invalidates every issued certificate.
- **Station state:** routers must `state.update()` + `setdefault`, never replace the dict — `/ingest/weight` and `/grade` interleave and would wipe each other's fields.
- **OpenAI Structured Outputs:** `strict: true` requires `additionalProperties: false` **and** every property in `required`, or the API 400s.
- **ESP32 Arduino core 3.x:** `ledcAttach(pin, freq, bits)` / `ledcWriteTone(pin, hz)`. Core 2.x's `ledcSetup`+channels does not compile. ArduinoJson **7**: `JsonDocument`, not `StaticJsonDocument`.
- **Windows consoles are cp1252** — any script printing emoji needs `sys.stdout.reconfigure(encoding="utf-8", errors="replace")`.
- **`.next` cache corrupts** if a production build and dev server share it. "Could not find the module … in the React Client Manifest" = `rm -rf .next && npm run dev`. **Do not debug the code.**

---

## Verify before claiming done

```bash
cd backend && .venv/Scripts/python -m pytest -q          # all green
.venv/Scripts/python evals/run_eval.py --mock            # exit 0
curl -s localhost:8000/healthz                           # adapters as expected
python scripts/simulate_station.py --scenario rush       # dashboard fills, cert VALID
cd frontend && npm run build                             # clean
grep -rl "SimulatedBadge" frontend/src                   # 3 payment surfaces + component
```

Never report a task done on a failing test, a partial implementation, or an unverified assumption. If something is broken, say so with the output.

---

## Never

- Let an LLM compute, adjust, round, or "sanity-check" a number.
- Write to Firestore from the frontend.
- Ship a payment surface without `<SimulatedBadge />`.
- Coerce an off-enum grade into a valid one.
- Commit `.env`, a service-account JSON, or a real key in `.env.example`.
- Add a second commodity, a fourth grade, or a real payment integration.
- Edit `main.py` or `strings.ts` if you don't own it.
- Quote the `--mock` eval accuracy as a model result — it's 1.0 by construction and proves only the harness.
