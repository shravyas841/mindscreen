# Benchmark Evidence

## Current submission evidence

- `submission_evidence.json` is the current evidence artifact.
- Regenerate it with `python backend/run_submission_evidence.py`.
- The script uses production PHQ-9, audio-scoring, fusion, HRE, and
  crisis-language functions. It supplies a fixed local text-score vector so the
  run has no external model or network dependency.
- The included language statements and modality profiles are constructed logic
  checks. They are not participant data or clinical validation.
- `current_weight_sensitivity.json` contains the deterministic sensitivity
  analysis across
  equal, text-dominant, audio-dominant, PHQ-dominant, and production weights.
  It reports raw fusion, the heuristic temperature transform, and post-HRE
  behavior separately. The constructed cases have no clinical labels, so no
  accuracy or optimal-weight claim is made. `submission_evidence.json` keeps a
  compact summary and points to the full artifact.
- Timing covers local function calls only. It excludes HTTP, database access,
  browser audio extraction, application rendering, and external APIs.
- Memory values are Python `tracemalloc` peaks, not process RSS or deployment
  memory.

## Historical artifacts

`p1_p5_sensitivity_raw.json`, `raw_latency_measurements.json`,
`latency_raw_trace.json`, `hre_masking_scenarios_raw.json`, and
`crisis_disambiguation_trace.json` were generated before the current safety
semantics. They remain for provenance but are not current evidence. Their
generating scripts are marked as legacy; the current sensitivity summary is
under `weight_sensitivity` in `submission_evidence.json` and the complete
current output is in `current_weight_sensitivity.json`.
