"""Vision-grader eval harness.

Real run: every image in golden_set/ with a label in expected_grades.json is
graded 3 times at temperature 0. Reports per-image results, overall accuracy
(majority-of-3 vs label), and stability (3/3 agreement rate). Writes
results/accuracy.json and exits 1 if accuracy < 0.80.

--mock: runs the same harness against the MockGrader on 3 synthetic images it
generates itself, so the loop is testable with no key and no photos.
"""

import argparse
import io
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from PIL import Image  # noqa: E402

from app.services.vision_grader import MockGrader, OpenAIGrader  # noqa: E402

EVALS_DIR = Path(__file__).resolve().parent
GOLDEN_DIR = EVALS_DIR / "golden_set"
RESULTS_DIR = EVALS_DIR / "results"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}
CALLS_PER_IMAGE = 3
ACCURACY_GATE = 0.80


def synthetic_cases(grader) -> list[tuple[str, bytes, str]]:
    """3 deterministic JPEGs; labels are the mock grader's own deterministic
    output, so a correct harness scores 1.0 by construction."""
    colors = {
        "vivid_red": (211, 30, 26),
        "dull_orange_red": (186, 116, 58),
        "dark_brown": (88, 52, 38),
    }
    cases = []
    for name, rgb in colors.items():
        img = Image.new("RGB", (256, 256), rgb)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        data = buf.getvalue()
        cases.append((f"synthetic_{name}.jpg", data, grader.grade(data).grade))
    return cases


def golden_cases() -> list[tuple[str, bytes, str]]:
    labels_path = GOLDEN_DIR / "expected_grades.json"
    if not labels_path.exists():
        sys.exit(f"missing {labels_path} — see golden_set/README.md")
    labels = json.loads(labels_path.read_text(encoding="utf-8"))
    cases = []
    for path in sorted(GOLDEN_DIR.iterdir()):
        if path.suffix.lower() in IMAGE_SUFFIXES and path.name in labels:
            cases.append((path.name, path.read_bytes(), labels[path.name]))
    if not cases:
        sys.exit("no labeled images in golden_set/ — see golden_set/README.md")
    return cases


def run(grader, cases) -> dict:
    per_image = []
    for name, image_bytes, expected in cases:
        grades = [grader.grade(image_bytes).grade for _ in range(CALLS_PER_IMAGE)]
        majority = Counter(grades).most_common(1)[0][0]
        result = {
            "image": name,
            "expected": expected,
            "grades": grades,
            "majority": majority,
            "correct": majority == expected,
            "stable": len(set(grades)) == 1,
        }
        per_image.append(result)
        mark = "OK " if result["correct"] else "MISS"
        print(f"[{mark}] {name}: expected={expected} got={grades} stable={result['stable']}")

    n = len(per_image)
    report = {
        "ranAt": datetime.now(timezone.utc).isoformat(),
        "grader": grader.name,
        "images": n,
        "callsPerImage": CALLS_PER_IMAGE,
        "accuracy": sum(r["correct"] for r in per_image) / n,
        "stability": sum(r["stable"] for r in per_image) / n,
        "perImage": per_image,
    }
    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / "accuracy.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\naccuracy={report['accuracy']:.2f} stability={report['stability']:.2f} -> {out}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mock", action="store_true", help="run against the mock grader on synthetic images")
    args = parser.parse_args()

    if args.mock:
        grader = MockGrader(latency_s=0)
        cases = synthetic_cases(grader)
    else:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            sys.exit("OPENAI_API_KEY not set — use --mock for the keyless harness check")
        grader = OpenAIGrader(api_key)
        cases = golden_cases()

    report = run(grader, cases)
    sys.exit(0 if report["accuracy"] >= ACCURACY_GATE else 1)


if __name__ == "__main__":
    main()
