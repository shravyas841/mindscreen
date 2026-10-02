# MindScreen evaluation package

This directory contains the scripts and checked-in JSON outputs used by the final paper. The two public text corpora are not redistributed.

## Method/version boundaries

- `crisis_v1.py` is the frozen original fixed-window filter used as the historical comparator.
- `crisis_v2.py` is the frozen clause-scoped method evaluated in the main crisis table.
- `crisis_v2_1.py` retains the post-hoc vocabulary ablation helper.
- `eval_posthoc.py` imports the released v2.1 filter from `backend/services/negation_service.py` for the v2.1 row.
- `fusion_analysis.py` imports the released PHQ, audio, calibration, and fusion functions from `backend/services/`.
- `latency.py` imports deployed local components but is Linux-specific. New latency runs must be reported with their new environment rather than compared as if measured on the paper's Xeon host.

The checked-in `results_*.json` files are the evidence record for the paper. Re-running a script overwrites its corresponding output, so review the Git diff and environment metadata before accepting a new result.

## Data layout

From this directory, clone the datasets into `data/`:

```bash
git clone --depth 1 https://github.com/ayaanzhaque/SDCNL.git data/SDCNL
git clone --depth 1 https://github.com/laxmimerit/twitter-suicidal-intention-dataset.git data/twitter-suicidal-intention-dataset
git -C data/SDCNL checkout ddf995aabd028657385cac6cee92c5d53774992d
git -C data/twitter-suicidal-intention-dataset checkout d800024117181614aa908c821400cede24e07355
```

The scripts expect:

```text
data/SDCNL/data/training-set.csv
data/SDCNL/data/testing-set.csv
data/twitter-suicidal-intention-dataset/twitter-suicidal_data.csv
```

## Run

```bash
python -m pip install -r evaluation/requirements-lock.txt
cd evaluation
python fusion_analysis.py
python eval_crisis.py
python eval_posthoc.py
python verify_hashes.py
```

On a Linux host, a new environment-labelled latency run can be collected with:

```bash
taskset -c 0 python latency.py
```

## Outputs

- `results_fusion.json`: uniform synthetic design-space scan and modality comparisons.
- `results_crisis.json`: SDCNL/Twitter v1/v2 metrics, confidence intervals, McNemar tests, and constructed suite.
- `results_posthoc.json`: deployed v2.1, ablation, and miss breakdown.
- `results_latency.json`: original paper latency values and recorded host details.
- `FROZEN_SHA256.txt`: manifest checked by `verify_hashes.py`.

The corpus metrics cannot be reproduced without separately acquiring the datasets. Their labels are noisy proxies and the results are not clinical validation.
Exact commits and CSV hashes are recorded in `evaluation/DATASET_REVISIONS.md`.
