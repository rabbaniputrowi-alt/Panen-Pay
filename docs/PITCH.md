# Panen Pay — Pitch

## The problem

At the chili intake desk, three things cost farmers money and have no paper
trail: disputed grades ("that's not fresh"), disputed weights ("my scale says
less"), and missing records (nothing to show a bank). The cooperative absorbs
the arguments; the farmer absorbs the losses.

## The evidence layer

Panen Pay doesn't move money and doesn't replace anyone. It makes the intake
moment *provable*: a photo-based grade with stated visual evidence, a live
load-cell weight, a deterministic price, and a GPS-timestamped certificate
whose SHA-256 hash makes tampering visible to anyone with the QR. Language
discipline: **"evidence layer," never "middleman killer."** Infrastructure for
the existing cooperative channel.

## Closing ask A — bank-agent channel pilot (primary)

> Pak Prihadiyanto — one cooperative, one season, one bank agent. Every intake
> gets a certificate; at season's end the farmer walks into the bank agent's
> kiosk with a verifiable cash-flow history instead of a story. We'd like BRI's
> agent-channel team to define what that file needs to contain to count as
> alternative data.

## Closing ask B — machinery dealer channel pilot (alternate)

> Dr. Arief Budiman — the same certificate trail that de-risks a working-capital
> loan de-risks an equipment lease. One dealer, one coop cluster: use certified
> intake volume as the underwriting signal for a small dryer or pump financed
> against next season's certified throughput.

Choose A or B in the floor-11 waiting area based on who is in the room.

## Q&A bank

**"Can't the operator just forge a certificate?"**
Only the server writes; clients are read-only by rule (R2). Every certificate
is a SHA-256 over the canonical transaction — change one field and public
verification fails.

**"Why aren't payments real?"**
Payments are a licensing problem; evidence is a technology problem. We built
the part a hackathon can prove — every payment surface is badged SIMULATED,
deliberately.

**"Isn't this just an LLM wrapper?"**
The LLM never touches a number. Every price and total comes from a pure,
unit-tested pricing engine; the model only picks one of three enum values and
explains what it saw. Output that invents a digit is rejected automatically.

**"Why would a bank care?"**
A season of certificates is verifiable cash-flow history — alternative data,
delivered through the coop as the community channel the bank already trusts.

**"How accurate is the grading?"**
Quote the eval number from `backend/evals/results/accuracy.json` (golden set,
3 calls per image, temperature 0). Low-confidence grades surface a retake
button and the operator override is itself logged.
