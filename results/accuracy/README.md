# Inspection report to approval note: accuracy

Measured on 12 Sep 2026 with `scripts/eval_inspection_accuracy.py`, running the
whole agent on local models (llama3 and moondream through Ollama) and scoring
the Word approval note it writes, which is the document an engineer would sign.

**Test set:** 2 synthetic pump reports (P-101, critical; P-202, high), each in
3 forms: a PDF with a text layer (table layout), a scanned PDF with no text
layer, and a scanned PNG. Ground truth is in
`demo_data/inspection/ground_truth_P101.json` and `ground_truth_P202.json`.

| Approval note | Before (`cc2a6e6`) | After |
|---|---|---|
| Fields correct | 58/111 (52.3%) | **108/111 (97.3%)** |
| Reading values | 22/36 | 36/36 |
| Reading limit status | 15/36 | 36/36 |
| Severity | 3/6 | 6/6 |
| Equipment tag | 3/6 | 6/6 |
| Recommendations | 15/27 | 24/27 |
| Silent misses (reading missing, no warning) | 14 | 0 |
| Figures in the note found in neither report nor SOP | 0 | 0 |
| Notes marked "SOURCED & VERIFIED" while wrong | 0 to 1 (varied between runs) | 0 |

Files: `note_baseline.json` (before), `note_after.json` (after),
`extract_after.json` (extraction and checks alone, no LLM).

## What was wrong before

- **Scanned PDFs scored 0.** A PDF with no text layer reached the pipeline as an
  empty string; OCR ran only on image files.
- **OCR dropped a critical reading.** RapidOCR's text-direction classifier
  turned one line of the P-101 scan upside down and dropped the seal-leakage
  line (14 drops/min against a limit of 5) without any warning.
- **Severity was a keyword guess.** Any mention of words like "critical" or
  "leak" anywhere in the text set it, including in phrases like "no leak".
- **No reading was compared with a limit.** The note's findings were report
  lines copied verbatim, plus whatever the vision model said about the page.
- **The claim checker ignored numbers.** It matched words of three letters or
  more, so "7.4" was dropped and "vibration is 4.2 mm/s" still passed.

## What changed

- **Reading:** scanned PDFs are OCR'd, with the direction classifier off and
  skewed pages straightened. Each OCR line keeps its confidence.
- **Extraction** (`backend/documents/inspection_extractor.py`): reads the tag,
  date, report number, every reading, the inspector's own verdicts, findings and
  recommendations from both narrative and table layouts, and keeps the report
  line each value came from.
- **Checks** (`backend/documents/inspection_checks.py`): readings are compared
  with SOP-M-104 limits (vibration zones §3, bearing temperature and seal leakage
  §4), or with ranges the report states. Severity follows a written rule from
  those results. Anything doubtful becomes a review item: a disagreement with
  the report's own verdict, a required reading that is missing, a findings value
  that contradicts the table, a limit that differs from the SOP, a low-confidence
  OCR line, or a missing date.
- **Approval note:** built only from the checked values, with no model text. It
  has a table of reading, line, limit, source and check result, lists the review
  items, and includes a sign-off block. It says "SOURCED & VERIFIED" only when
  there is nothing to review, and even then states that an engineer must sign.
- **Verifier:** every figure in a model claim must appear in the report or the
  retrieved SOPs, or the claim is marked unsupported.

## What these numbers do not show

- Only 2 reports, both synthetic and made by the team. Real plant reports will
  be messier. The founding plan's target is 200+ real reports.
- The 3 remaining misses are one ground-truth recommendation worded differently
  from anything in the report ("increase ... to daily intervals until overhaul
  window" against "Monitor triaxial vibration daily ..."). The note quotes the
  report's own line.
- Limits are configured for SOP-M-104 only. Other readings are checked against
  ranges the report states, or shown as "as stated" when it gives no number.

## Reproduce

```bash
python scripts/eval_inspection_accuracy.py --stage extract
python scripts/eval_inspection_accuracy.py --stage note --out results/accuracy/note_after.json
python -m pytest tests/test_inspection_checks.py
```
