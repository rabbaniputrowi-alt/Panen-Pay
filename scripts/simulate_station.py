"""Panen Pay station simulator — first-class demo backup (R7).

Replicates the ESP32 station exactly, with no hardware attached: ramps weight
0→N grams with jitter, marks stable after 1.5s of <5g spread, POSTs
/ingest/weight, polls /station/feedback and prints the tone it would play.

Dependencies: httpx + stdlib only (images are hand-encoded PNGs via zlib).

  python scripts/simulate_station.py --scenario happy     # one farmer, 2.4 kg
  python scripts/simulate_station.py --scenario rush      # 5 farmers, random
  python scripts/simulate_station.py --weight 3.2 --loop  # scale only, forever
"""

import argparse
import random
import struct
import sys
import time
import zlib

import httpx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

STATION_ID = "station-1"
GPS_BASE = (-7.797068, 110.370529)

TONES = {
    "fresh": "🔊 fresh tone (1047→1319 Hz, ascending)",
    "sell_today": "🔊 sell_today tone (880 Hz)",
    "wilted": "🔊 wilted tone (587→440 Hz, descending)",
    "error": "🔊 error tone (220 Hz)",
}
STABLE_CHIRP = "🔊 stable chirp (1568 Hz, 80 ms)"

FARMERS = ["Bu Sari", "Pak Budi", "Bu Tini", "Pak Joko", "Bu Rahma"]

def make_png(rgb: tuple[int, int, int], size: int = 64) -> bytes:
    """Minimal solid-color PNG encoder — keeps the simulator stdlib-only."""

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    row = b"\x00" + bytes(rgb) * size
    idat = zlib.compress(row * size)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", idat)
        + chunk(b"IEND", b"")
    )

def post_weight(client: httpx.Client, grams: float, stable: bool) -> None:
    client.post(
        "/api/v1/ingest/weight",
        json={"station_id": STATION_ID, "weight_grams": round(grams, 1), "stable": stable},
    ).raise_for_status()

def ramp_to(client: httpx.Client, target_grams: float) -> None:
    """Load the basket: jittered ramp, then 1.5s of <5g spread → stable."""
    grams = 0.0
    step = max(target_grams / 12, 40)
    while grams < target_grams:
        grams = min(grams + step + random.uniform(-15, 15), target_grams)
        post_weight(client, max(grams, 0), stable=False)
        print(f"  ⚖️  {grams:7.1f} g (settling)")
        time.sleep(0.15)

    settle_until = time.monotonic() + 1.5
    while time.monotonic() < settle_until:
        post_weight(client, target_grams + random.uniform(-2, 2), stable=False)
        time.sleep(0.25)
    post_weight(client, target_grams, stable=True)
    print(f"  ⚖️  {target_grams:7.1f} g STABLE — {STABLE_CHIRP}")

def poll_feedback(client: httpx.Client, timeout_s: float = 10.0) -> str:
    """Poll every 2s like the firmware; print the tone instead of sounding it."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        tone = client.get(
            "/api/v1/station/feedback", params={"station_id": STATION_ID}
        ).json()["tone"]
        if tone != "none":
            print(f"  {TONES.get(tone, TONES['error'])}")
            return tone
        time.sleep(2)
    print("  (no feedback tone within timeout)")
    return "none"

def run_transaction(client: httpx.Client, farmer: str, target_grams: float) -> None:
    print(f"\n=== {farmer}: {target_grams / 1000:.2f} kg batch ===")

    color = (random.randint(120, 230), random.randint(20, 130), random.randint(15, 60))
    photo = make_png(color)
    grade = client.post(
        "/api/v1/grade", files={"photo": ("batch.png", photo, "image/png")}
    ).raise_for_status().json()
    print(f"  📷 graded: {grade['grade']} ({grade['confidence']}) — {grade['visual_evidence']}")

    ramp_to(client, target_grams)

    gps = {
        "lat": GPS_BASE[0] + random.uniform(-0.002, 0.002),
        "lng": GPS_BASE[1] + random.uniform(-0.002, 0.002),
    }
    body = client.post(
        "/api/v1/transactions",
        json={"farmerName": farmer, "gps": gps, "stationId": STATION_ID},
    ).raise_for_status().json()
    tx, cert = body["transaction"], body["certificate"]
    print(f"  💰 Rp{tx['totalIdr']:,} ({tx['weightKg']} kg × Rp{tx['pricePerKg']:,}/kg) [paid_mock]")
    print(f"  📜 {cert['qrPayloadUrl']}  sha256:{cert['sha256'][:12]}…")
    print(f"  📝 {body['brief']}")
    poll_feedback(client)

def scenario_happy(client: httpx.Client) -> None:
    run_transaction(client, "Bu Sari", 2400)

def scenario_rush(client: httpx.Client) -> None:
    for farmer in FARMERS:
        run_transaction(client, farmer, random.uniform(500, 5000))
        time.sleep(0.5)

def weight_only(client: httpx.Client, weight_kg: float, loop: bool) -> None:
    while True:
        ramp_to(client, weight_kg * 1000)
        if not loop:
            return
        print("  (re-zeroing scale)")
        post_weight(client, 0, stable=False)
        time.sleep(1)

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", default="http://localhost:8000")
    parser.add_argument("--scenario", choices=["happy", "rush"])
    parser.add_argument("--weight", type=float, help="ramp the scale to this many kg (no transaction)")
    parser.add_argument("--loop", action="store_true", help="with --weight: repeat forever")
    args = parser.parse_args()

    with httpx.Client(base_url=args.api, timeout=30) as client:
        try:
            health = client.get("/healthz").json()
        except httpx.HTTPError as exc:
            sys.exit(f"backend not reachable at {args.api}: {exc}")
        print(f"connected to {args.api} (grader={health['grader']}, store={health['store']})")

        if args.scenario == "happy":
            scenario_happy(client)
        elif args.scenario == "rush":
            scenario_rush(client)
        elif args.weight is not None:
            weight_only(client, args.weight, args.loop)
        else:
            parser.error("pick --scenario happy|rush or --weight N")

if __name__ == "__main__":
    main()
