# MindScreen: evaluation code and system patches

## evaluation/
Reproduces every number in the revised paper.

    # 1. fetch the public corpora (not redistributed here)
    mkdir -p ../data && cd ../data
    git clone --depth 1 https://github.com/ayaanzhaque/SDCNL.git
    git clone --depth 1 https://github.com/laxmimerit/twitter-suicidal-intention-dataset.git
    cd ../evaluation
    pip install pandas numpy scipy scikit-learn
    python3 eval_crisis.py        # Table VI main rows, Fig. 2, constructed suite
    python3 eval_posthoc.py       # ablation, v2.1, v1 miss breakdown, lexicon ceiling
    python3 fusion_analysis.py    # Tables IV and V, modality ablation
    taskset -c 0 python3 latency.py   # Table VII (numbers depend on hardware)
    sha256sum -c FROZEN_SHA256.txt

The scripts expect the data folder at `../data/` next to `evaluation/`.

- `crisis_v1.py` is the deployed filter, a verbatim copy of `backend/services/negation_service.py`.
- `crisis_v2.py` is the evaluated revision.
- `crisis_v2_1.py` is v2 plus self-harm triggers (the released version). It also contains the ablation that combines v2's scoping rules with v1's vocabulary.
- `orig_services/` holds verbatim copies of the deployed PHQ, audio and calibration services, which `fusion_analysis.py` uses.

## patches/
These are drop-in replacements for the same paths in the MindScreen repository. See REVISION_NOTES.md, section 3.
