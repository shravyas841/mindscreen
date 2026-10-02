# MindScreen final reconciliation report

Date: 2026-10-01
Branch: `reconciliation-final-ieee`
Authoritative paper reviewed: `MindScreen_Final_IEEE_Submission (1).pdf`
Implementation baseline: `mindscreen-main (12).zip`

The IEEE paper and its checked-in LaTeX source were not edited.

## A. Starting-state audit

The uploaded ZIP already contained the v2.1 clause-scoped crisis filter, R0/R1/R2 code in the fusion service, browser acoustic extraction, and the final evaluation bundle. The implementation was not internally consistent at its API and UI boundaries:

- **CRITICAL:** `predict.py` rebuilt `crisis_flag` from the final tier, causing PHQ-floor and non-crisis High Priority outcomes to be reported as explicit crisis detections.
- **CRITICAL:** the PHQ-only route did not apply R1; an Item 9 endorsement with a low total could remain minimal or mild.
- **HIGH:** the response schema discarded `resource_display_flag`, `phq_floor_applied`, and missing-audio status.
- **HIGH:** protected routes silently used a generated demo user and ignored bearer tokens; refresh always returned 501.
- **HIGH:** dashboard, mood, history, and counselor screens displayed fabricated records or trends.
- **HIGH:** evaluation fusion code imported duplicated `orig_services` rather than the released implementation.
- **MEDIUM:** the paper's minimal-band PHQ vector was `{0.80, 0.15, 0.04, 0.01}`, while code used `{0.80, 0.15, 0.05, 0.00}`.
- **MEDIUM:** skipped audio was correctly omitted by the primary fusion path, but legacy neutral-feature and Base64-size fallbacks remained available in code and documentation.
- **MEDIUM:** dependency ranges were unpinned and the initial npm lock resolved eight reported vulnerabilities.
- **MEDIUM:** existing top-level Python files were executable scripts with assertions and print statements; pytest collected zero tests.

## B. Implemented changes

- Centralised the deployed weights, present-modality renormalisation, and R0/R1/R2 logic in `backend/services/fusion_service.py`.
- Preserved the default 0.50/0.30/0.20 ratio and the fixed `T=1.20` transform.
- Added `priority_score` while retaining `confidence` as a compatibility alias.
- Separated `crisis_flag` (R1/R2 only) from `resource_display_flag` (explicit crisis or final High Priority).
- Corrected PHQ-only R1 behavior and aligned the minimal PHQ vector with the paper.
- Removed neutral-audio and Base64-size scoring from the deployed audio service. Missing audio is omitted and weights are renormalised.
- Aligned the acoustic boundary so 0.65 remains Moderate and values above 0.65 are High Priority, matching the paper's table.
- Exposed `audio_present`, `phq_floor_applied`, and text inference source in API responses.
- Replaced misleading UI terms such as calibrated probability, clinical-grade, biomarkers, MentalBERT, and SHAP with implementation-accurate language.
- Made Tele-MANAS the primary resource throughout the backend, UI, and deployment configuration.
- Implemented access-token validation, refresh-token validation/rotation, active-user checks, password bounds, disclaimer acknowledgement, and route rate limits.
- Removed demo-user bypasses, fabricated dashboards/history/counselor data, dead scripts, duplicate patch copies, and unused assets.
- Stopped persisting journal text and audio. PHQ responses, mood entries, and result records remain stored.
- Added pinned backend/evaluation dependencies, deterministic npm installation, production secret checks, and fail-closed production database startup.
- Rewrote the root and evaluation READMEs around the actual system and evidence boundaries.

## C. Quantitative claim reconciliation

| Paper claim | Verification source | Result |
|---|---|---|
| Under-triage 37.0%, 55.3%, 85.2% in PHQ bands 5–9, 10–14, 15–19 | `evaluation/fusion_analysis.py` → `results_fusion.json` | Re-run through deployed fusion helper; exact match |
| R0 under-triage 0% in every PHQ band | `results_fusion.json`; safety tests | Re-run; exact match |
| 119 text states × 51 audio states = 6,069 configurations per PHQ total | `fusion_analysis.py`; `results_fusion.json` methodology | Verified |
| Text-overrides-PHQ threshold 0.288 | Algebra encoded by stated vectors/weights | Consistent; not a population statistic |
| SDCNL n=379, 193 positive, 186 negative | acquired SDCNL test CSV; `results_crisis.json` | Re-run; exact match |
| Twitter n=8,785, 3,958 positive, 4,827 negative | acquired Twitter CSV; `results_crisis.json` | Re-run; exact match |
| v1 sensitivity 22.8%/24.2%, specificity 86.6%/87.9% | `eval_crisis.py` → `results_crisis.json` | Re-run; exact match |
| v2 sensitivity 55.4%/51.3%, specificity 75.8%/91.7% | `eval_crisis.py` → `results_crisis.json` | Re-run; exact match |
| v2.1 sensitivity 55.4%/52.2%, specificity 72.0%/91.7% | deployed filter via `eval_posthoc.py` → `results_posthoc.json` | Re-run; exact match |
| McNemar p=3.5×10^-11 on SDCNL positives | `results_crisis.json` | Re-run value 3.4675×10^-11 |
| TF-IDF+LR Twitter AUROC 0.532 and specificity 24.3% | `results_crisis.json` | Re-run; exact match after rounding |
| PHQ 0.002 ms, acoustic 0.008 ms, v2 0.450 ms; p95 0.003/0.012/1.320 ms | `results_latency.json` | Raw means/p95 round to paper values |
| Peak heap 0.06 MB | `results_latency.json` | Raw value 0.05915 MB |

Dataset commits and CSV SHA-256 values are recorded in `evaluation/DATASET_REVISIONS.md`. Frozen method and result hashes are checked by `evaluation/verify_hashes.py`.

The latency benchmark was not rerun on this Windows workstation because that would not reproduce the paper's Linux Xeon single-core environment. The raw JSON explicitly records Python 3.11.15, Intel Xeon 2.1 GHz, CPU affinity 1, and Linux resource measurements. Its values match the paper after rounding.

## D. Experiment and reproducibility changes

- Fusion analysis now imports released backend PHQ, audio, calibration, and fusion functions.
- Post-hoc v2.1 evaluation now imports the released crisis filter.
- Frozen v1 and v2 remain separate because the paper compares historical method versions.
- Dataset commits and file hashes are pinned.
- A verifier covers frozen comparison methods, the deployed v2.1 filter, and all final JSON evidence files.
- Historical benchmark files were moved under `benchmarks/historical/` and explicitly excluded as paper evidence.
- Evaluation imports no longer trigger another evaluation as a side effect.

## E. Test coverage and results

Backend pytest coverage now includes:

- all PHQ band boundaries and the paper's minimal-band vector;
- deployed weights and missing-audio renormalisation;
- R0, R1, R2, priority-score floor, and crisis/resource separation;
- affirmative, negated, third-party, idiomatic, and distress-only language;
- JWT registration, login, access validation, refresh validation, and token-type rejection;
- API preservation of safety flags and PHQ-only Item 9 behavior;
- rejection of audio scoring without real descriptors.

Frontend tests cover short/unusable recording behavior and acoustic aggregation. Final verification: **41 backend tests passed**, **3 frontend tests passed**, TypeScript/Vite production build passed, npm audit reported **0 vulnerabilities**, and all frozen evidence hashes passed.

## F. Security, privacy, and deployment review

Resolved:

- bearer tokens are now enforced;
- refresh tokens are validated and rotated;
- production rejects the default secret;
- production database failure is fail-closed instead of silently switching to local SQLite;
- registration/login/prediction/chat routes have rate limits;
- journal text and audio are not persisted;
- `.env`, databases, local datasets, virtual environments, and build output are ignored;
- no committed secrets or databases were found;
- Render uses pinned backend requirements and Vercel uses `npm ci`.

Remaining operational gaps:

- no application-level encryption-at-rest, retention/deletion workflow, audit log, token revocation list, or formal consent record versioning;
- the database schema is created at startup and the repository has no complete migration history for the reconciled state;
- third-party model calls send journal text to configured providers during a request;
- no deployed endpoint was exercised in this local audit.

These gaps preclude a legal compliance claim and any use with real participant or patient data.

## G. Documentation and repository cleanup

The README now describes the actual model, fallback behavior, safety flags, missing-modality handling, evidence files, environment limits, authentication, and privacy gaps. Unsupported live-deployment claims were removed. Dead experimental scripts, duplicated patch copies, unused UI assets, and fabricated user-facing records were removed. Historical raw artifacts remain under a clearly labelled archive for provenance.

## H. Remaining paper discrepancies

The following statements remain in the authoritative paper because the instruction prohibited paper edits:

- **CRITICAL:** the paper says persistence adheres to India's DPDP Act. The repository cannot substantiate legal compliance; several governance controls remain absent.
- **HIGH:** Table VI labels v1 as “deployed,” while the reconciled deployed filter is v2.1. v1 is now only the frozen historical comparator.
- **HIGH:** the conclusion says the deployed weighting under-triages, while the deployed R0 safety layer prevents final-tier under-triage. The 37.0/55.3/85.2 values describe baseline fusion before R0 (with the historical S≥20 rule), not current final output.
- **HIGH:** the code-availability section links `ruchita0131/mindscreen`, not the user's authoritative fork/branch.
- **MEDIUM:** claims that test corpora were not used in development and were used within their terms cannot be independently proven from code. The archived notes state that only SDCNL training data informed vocabulary work, but this is a provenance statement rather than executable evidence.
- **MEDIUM:** latency covers local PHQ, acoustic, and rule-filter computation. It excludes remote Hugging Face and Gemini request latency and should not be read as full request latency.

## I. Submission-readiness assessment

The implementation and evidence package are materially more consistent and reproducible. The central research numbers were independently re-run from the acquired public datasets and match the paper, while the design-space results now call deployed code. The application now implements the stated safety behavior at both service and API boundaries.

The project is suitable for a college major-project demonstration and for submission as a clearly limited research prototype after the paper discrepancies in Section H are corrected. It is not ready for clinical deployment, participant-data collection, or a submission that asserts DPDP compliance. The strongest supported contribution is the measured comparison of the frozen crisis filters plus the synthetic demonstration that R0 prevents PHQ-relative under-triage by construction.
