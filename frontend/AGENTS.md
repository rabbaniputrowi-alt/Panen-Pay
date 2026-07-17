# frontend/ — lane instructions (Bani)

This directory is **Next.js 16 + Tailwind v4 + React 19** — newer than most training data. When an API looks unfamiliar, read the bundled docs in `node_modules/next/dist/docs/` before writing code. Do not pattern-match from Next 14 / Tailwind v3 tutorials.

The root `AGENTS.md` rules (R1–R7, ownership, contract) apply here in full. This file adds the frontend-only detail.

---

## Map

```
src/
├── app/
│   ├── (station)/page.tsx        # "/" — 4-step intake: photo → grade → weigh → done
│   ├── (dashboard)/dashboard/    # "/dashboard" — live coop feed (English-only surface)
│   ├── cert/[id]/                # "/cert/:id" — public QR verification page
│   │   ├── page.tsx              # server component: await params, hand off
│   │   └── CertVerify.tsx        # client component: fetches ?verify=1
│   ├── layout.tsx                # Jakarta Sans, lang="id", metadata from strings
│   └── globals.css               # @theme tokens — this IS the Tailwind config
├── components/                    # SimulatedBadge · TierChip · WeightLive · GradeCard · CertificateQR
└── lib/
    ├── strings.ts                # EVERY user-facing string, { id, en } pairs
    ├── api.ts                    # typed wrappers — the ONLY fetch path
    ├── data.ts                   # useRecentTransactions: poll ⇄ firestore
    └── firebase.ts               # web SDK, READ-ONLY, no Analytics
```

Route groups `(station)`/`(dashboard)` do not appear in URLs. There must be **no** `src/app/page.tsx` — it would collide with `(station)/page.tsx` at `/` and fail the build.

---

## Non-negotiables in this directory

- **All fetches go through `lib/api.ts`.** Never call `fetch()` directly in a component; never hardcode a URL. Base URL is `NEXT_PUBLIC_API_BASE` (baked at **build** time — changing it on Vercel requires a redeploy).
- **All copy goes through `lib/strings.ts`** as `{ id, en }`. Station + cert pages render `.id` large with `.en` as a small subtitle; the dashboard renders `.en` only. A hardcoded UI string anywhere else is a bug.
- **Read-only client (R2).** No Firestore writes, no client-side hash checks — certificate validity is the server's `valid` boolean from `?verify=1`, displayed verbatim.
- **The only arithmetic allowed** is the dashboard's `reduce` sums over engine-computed numbers. Never compute `weight × price` in the client (R1).
- **`<SimulatedBadge />` on every payment surface** (R3): station done-screen, dashboard payments column, cert page total.
- **Reuse the five components** — do not create a second badge, chip, or QR renderer.

## Framework traps (all bit once already)

- `params` in dynamic routes is a **`Promise`**: `const { id } = await params;` in an async server component, then pass plain props to a `"use client"` child.
- Tailwind v4: tokens live in the `@theme` block in `globals.css` (`--color-leaf` → `bg-leaf`). **No `tailwind.config.ts` exists; do not create one.**
- Locked palette: canvas `#FAFBF0` · leaf `#3F7D3A` · gold `#E9B62C` (dark text on it — white fails contrast) · terra `#C0653F` · slate `#5B6B7A`.
- SWR polls **must** pass `refreshWhenHidden: true` (WeightLive at 1s, dashboard at 2s) — hidden/mirrored displays silently pause polling otherwise.
- Plain `<img>` for camera `blob:` URLs and the QR `data:` URI — `next/image` can't optimize either.
- `firebase.ts`: `getApps()[0] ?? initializeApp(config)` (Fast Refresh re-runs modules), **never** import `getAnalytics` (SSR crash). The web config is public by design — do not "hide" it in an env var.
- Camera input: `accept="image/*" capture="environment"`, clear `e.target.value` after reading (same-file re-pick), `URL.revokeObjectURL` old thumbnails.
- Station UX: primary buttons `min-h-20` — the operator wears gloves. Bahasa first, English subtitle.
- "Could not find the module … in the React Client Manifest" after mixing `npm run build` with a running dev server → `rm -rf .next && npm run dev`. The code is fine.

## Verify

```bash
npm run build        # must be clean before any merge
npm run dev          # manual flow against local backend on :8000
# weigh step: python scripts/simulate_station.py --weight 2.4  (from repo root)
```
