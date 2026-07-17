# Golden set

Drop ~20 labeled chili photos here before the real eval run.

- Files: `.jpg` / `.jpeg` / `.png`, one harvest batch per photo.
- Labels: `expected_grades.json` maps filename → `fresh` | `sell_today` | `wilted`:

```json
{
  "batch_001.jpg": "fresh",
  "batch_002.jpg": "wilted"
}
```

Then run `python backend/evals/run_eval.py` with `OPENAI_API_KEY` set.
The accuracy number it prints goes on the Prasojo slide.
