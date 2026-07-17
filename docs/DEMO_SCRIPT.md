# Demo script (5 minutes)

## Arc

| Time | Beat |
|---|---|
| 0:00–0:30 | **Farmer story.** Bu Sari sells 2.4 kg of chili. Today the grade is an argument, the scale is a mystery, and the receipt doesn't exist. Show the photo of a real intake desk. |
| 0:30–2:30 | **Live grade–weigh–certify.** Photograph the batch on stage → grade card appears (name the tier + the visible evidence). Place it on the scale → dashboard weight ramps live → stable chirp. Confirm → certificate screen: total, QR, SIMULASI badge. Phone scans the QR → verification page shows VALID. |
| 2:30–3:15 | **Dashboard on the second screen.** Rush scenario has been running: feed fills, totals strip climbs. Point at the payments column: every row says simulated — on purpose. |
| 3:15–4:15 | **Credit-trail slide.** A season of hashed certificates = verifiable cash-flow history for a farmer who has never had one. The coop becomes the community channel for MSME credit scoring. |
| 4:15–5:00 | **The ask** (choose A or B in the floor-11 waiting area — see PITCH.md). |

## Pre-room checklist

- [ ] Run the **hardware path** once end-to-end (ESP32 + scale + buzzer).
- [ ] Run the **simulator path** once end-to-end (`--scenario happy`, then `rush`).
- [ ] Phone hotspot fallback configured (`#define` block in station.ino + laptop IP).
- [ ] Display mirror mode tested; dashboard zoomed to readable size.
- [ ] Offline copies of every slide on the laptop AND the phone.
- [ ] `GET /healthz` returns ok before walking in.
- [ ] Battery: laptop charged, power bank for the ESP32.
