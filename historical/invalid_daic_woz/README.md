# Invalid historical DAIC-WOZ experiment

This directory is quarantined historical material. It is not part of the
production application, automated tests, or authoritative evidence generated
by `backend/run_submission_evidence.py`.

The former tracked `*_COVAREP.csv` files were HTML file-index pages rather than
acoustic feature CSVs and have been removed. The former tracked DAIC-WOZ label
files were also removed to avoid redistributing licensed dataset material.

`train_daicwoz_audio.py` synthesizes feature vectors using label-dependent
distributions. That creates target leakage, does not use the production
six-descriptor acoustic path, and cannot support accuracy, generalization, or
clinical claims. The downloader scripts contain old machine-specific paths and
are retained only to explain repository history. Do not execute or cite these
scripts as current evidence.

No current evidence or production module imports this directory.
