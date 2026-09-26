# MindScreen Research Manuscript Status

This Markdown file is retained as a concise companion to the authoritative manuscript,
[mindscreen_ieee_paper.tex](mindscreen_ieee_paper.tex). The earlier draft contained
obsolete architecture descriptions and unsupported performance figures; those claims
have been removed. Submission text and numerical results must be taken from the LaTeX
source and its compiled PDF.

## Evidence-grounded prototype summary

MindScreen is an academic engineering prototype for mental-health screening support.
It combines fixed PHQ-9 score vectors, hosted emotion classification with a deterministic
local fallback, and six browser-extracted acoustic descriptors using manually selected
late-fusion weights:

- text: 0.50
- audio: 0.30
- PHQ-9: 0.20

The text classifier is an affective proxy, not a depression classifier. Acoustic scoring
uses a heuristic mapping and has not been trained or validated as a clinical biomarker.
The fused scores and the temperature transformation are engineering scores, not calibrated
clinical probabilities.

The deterministic High-Risk Escalation rules are:

1. PHQ-9 total >= 20,
2. PHQ-9 Item 9 > 0, or
3. affirmative self-directed crisis language detected by the deterministic safety gate.

Any trigger produces the internal high-priority tier, a priority score of at least 0.90,
and resource display. The crisis flag is true only for Item 9 endorsement or affirmative
self-directed crisis language. A high total score alone does not assert acute crisis intent.

Skipped audio is represented as unavailable. The backend applies the documented prior
`[0.25, 0.45, 0.20, 0.10]` at the existing 30% audio weight; it does not fabricate an
observed acoustic feature vector. This policy has not been statistically validated.

## Reproducible repository evidence

Run:

```bash
python backend/run_submission_evidence.py
pytest
```

The saved output is `benchmarks/submission_evidence.json`. On the recorded local Windows
environment, the script verified four isolated HRE scenarios and matched all team-assigned
labels in a 17-statement constructed rule-verification corpus. This exact-set result is
not a clinical sensitivity or specificity estimate.

The same run measured the in-process deterministic local fusion function at 0.1889 ms
mean and 0.2035 ms P95 over 50 calls after 10 warm-up calls. These are function
microbenchmarks. HTTP, database, browser extraction, hosted API, network, concurrency,
Render-container, and end-to-end deployment latency remain unmeasured.

No repository evidence supports diagnostic accuracy, macro-F1, clinical false-negative
rates, DAIC-WOZ audio validation accuracy, or hosted Hugging Face/Gemini latency. No such
results are claimed by the authoritative manuscript.

## Limitations

The system is not a diagnostic or emergency medical device. It has not been clinically
validated. The rule-based crisis-language gate has limited linguistic coverage.
Authentication currently includes a demo-mode bypass and should not be described as secure.
Free text may be sent to hosted APIs without automatic PII redaction. Clinical effectiveness,
fairness, calibration, and real-world deployment performance remain future work.
