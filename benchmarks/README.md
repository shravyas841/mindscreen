# Benchmark Evidence

## Current submission evidence

- `submission_evidence.json` is the current evidence artifact.
- Regenerate it with `python backend/run_submission_evidence.py`.
- The script uses production PHQ-9, audio-scoring, fusion, HRE, and
  crisis-language functions. It supplies a fixed local text-score vector so the
  run has no external model or network dependency.
- The included language statements and modality profiles are constructed logic
  checks. They are not participant data or clinical validation.
- Timing covers local function calls only. It excludes HTTP, database access,
  browser audio extraction, application rendering, and external APIs.
- Memory values are Python `tracemalloc` peaks, not process RSS or deployment
  memory.

## Historical artifacts

`p1_p5_sensitivity_raw.json`, `raw_latency_measurements.json`,
`latency_raw_trace.json`, `hre_masking_scenarios_raw.json`, and
`crisis_disambiguation_trace.json` were generated before the current safety
semantics. They remain for provenance but are not evidence for the current
paper. Their generating scripts are marked as legacy.
