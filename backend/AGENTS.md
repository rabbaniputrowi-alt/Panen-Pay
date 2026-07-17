# backend/ — lane instructions (backend dev)

You own every number, every write, and every merge to `main`. FastAPI + Pydantic v2 + Python 3.11+. The root `AGENTS.md` (R1–R7, ownership, API contract) applies in full — this file adds the backend-only detail.

**Files in this directory you must NOT edit** (they're Bani's lane, even though they live here):
`app/services/vision_grader.py` · `app/services/brief_writer.py` · `app/routers/grade.py` · `tests/test_grading_schema.py` · `evals/`. If a task needs a change there, stop and say so.

---

## Map

```
backend/
├── requirements.txt              # 11 deps; grpcio is the slow install
├── pytest.ini                    # pythonpath=. — kills ModuleNotFoundError: app
├── app/
│   ├── main.py                   # create_app() factory — ONLY YOU edit this file
│   ├── config.py                 # Settings + build_adapters — the §E switchboard
│   ├── deps.py                   # get_store/get_grader/get_brief_writer/get_settings
│   ├── store.py                  # Store ABC + InMemoryStore + FirestoreStore
│   ├── models/schemas.py         # Tier Literal + camelCase models (locked shapes)
│   ├── routers/                  # ingest, station, transactions, certificates, health (yours)
│   └── services/
│       ├── pricing_engine.py     # THE numbers authority — pure, stdlib-only
│       ├── certificate_svc.py    # canonical JSON → SHA-256 → QR data-URI
│       └── mock_ledger.py        # 5 lines, deliberately — only "paid_mock" exists
└── tests/                        # oracle, tamper, integration (yours)
```

## Non-negotiables in this directory

- **`pricing_engine.py` is the only place a price is computed.** Pure functions, zero I/O, imports nothing but `decimal`. Routers call it; nothing reimplements it. Unknown tier → `ValueError`, weight outside [0.05, 10.0] → `ValueError`. Never silently default.
- **All writes go through the `Store` ABC.** Routers depend on `Depends(get_store)` and must never know which implementation they got. No direct `firebase_admin` usage outside `FirestoreStore`.
- **Every adapter decision lives in `config.py`'s `build_adapters`** — key present → real, absent → mock. Never check `os.environ` in a router.
- **App factory pattern:** `create_app(settings)` — tests build hermetic apps with `Settings(..., _env_file=None)`. Never module-level state that the factory doesn't own.
- **`main.py` is yours alone.** Mount Bani's `grade` router when asked; resolve any `main.py` merge conflict yourself.
- **Transaction assembly order is load-bearing:** 409 gates → engine → ledger → **hash** → attach back-refs → store → brief → consume `pendingGrade` → queue feedback. Payment fields exist *before* hashing; only `certificateHash`/`certId` attach after.

## Python traps (each one already bit once)

- `Decimal(str(x))`, never `Decimal(float)` — floats carry binary error into money.
- `ROUND_HALF_UP` explicitly — Python defaults to banker's rounding (Rp2.050 → Rp2.000 on stage). Never builtin `round()` for money.
- Canonical JSON = `json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)` — **frozen forever**; changing it invalidates every issued certificate.
- `_HASH_EXCLUDED_FIELDS = {"certificateHash", "certId"}` — anything attached to a transaction *after* hashing must be excluded, or every cert verifies INVALID.
- `pop_feedback` is **read-once**: `dict.pop(station_id, "none")`. The buzzer polls every 2s; a non-clearing read replays tones forever.
- `/ingest/weight` and `/grade` interleave in production: `state.update()` + `setdefault`, never replace the state dict, or the scale wipes the pending grade.
- `Settings.model_config` needs `extra="ignore"` (the shared `.env` has `NEXT_PUBLIC_*` keys) and `env_file=(".env", "../.env")` (uvicorn runs from `backend/`).
- Local `.env`: wrap `FIREBASE_SERVICE_ACCOUNT_JSON` in **single** quotes (dotenv keeps `\n` literal for `json.loads`); paste it **raw, unquoted** into Railway. Double quotes corrupt the PEM.
- Lazy-import `FirestoreStore`'s firebase deps inside `__init__`; guard with `if not firebase_admin._apps`.
- `list_recent_transactions` = reversed insertion order (dicts are ordered 3.7+) — a `createdAt` sort tie-breaks wrongly on same-second transactions.
- HTTP semantics: world-not-ready (no stable weight / no grade) → **409**; engine `ValueError` → **422**; `GradingError` → **502** (that mapping is Bani's router, don't change it).

## Deploy (Railway)

Root directory `backend`, start command — both flags mandatory or the deploy "succeeds" and 502s:
```
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```
Env vars may be empty — the app must boot keyless (`/healthz` → `{"grader":"mock","store":"memory"}`). After flipping Firestore live, immediately verify a cert survives the round-trip: `GET /api/v1/certificates/{id}?verify=1` must return `"valid": true` — type coercion in storage is the failure that passes locally and dies in prod.

## Verify before claiming done

```bash
.venv/Scripts/python -m pytest -q                       # all green (58 at full build)
.venv/Scripts/python -m uvicorn app.main:app            # boots keyless
curl -s localhost:8000/healthz                          # {"ok":true,"grader":"mock","store":"memory"}
```

Your gate-merge duty: `git merge --no-ff` every branch into `main` at G1/G2/G3/G4, backend-first, frontend-last. The only legal conflict is `main.py` — and it's yours.
