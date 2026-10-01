"""Fusion analyses bound to the released backend implementation."""
import json, itertools, sys
from pathlib import Path

import numpy as np

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = REPOSITORY_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from services.audio_service import _interpolate, get_audio_prediction
from services.calibration_service import apply_temperature_scaling
from services.fusion_service import fuse_probabilities
from services.phq_service import calculate_phq_score
K = ["minimal", "mild", "moderate", "severe"]
W = {"Equal": (1/3,1/3,1/3), "Text-dom": (.6,.2,.2), "Audio-dom": (.2,.6,.2), "PHQ-dom": (.2,.2,.6), "MindScreen": (.5,.3,.2)}

def vec(d): return np.array([d[k] for k in K])
def fuse(pt, pa, pq, w, T=1.2):
    raw = vec(fuse_probabilities(dict(zip(K, pt)), dict(zip(K, pq)), dict(zip(K, pa)),
                                 weights={"text":w[0], "audio":w[1], "phq":w[2]}))
    soft = vec(apply_temperature_scaling(dict(zip(K, raw)), T))
    return raw, soft

# ---------- (A) Table V recomputation with the manuscript's stated vectors ----------
P = {
 "P1": dict(S=22,q9=1, q=[0,.05,.15,.80], t=[.05,.05,.05,.85], a=[.03,.13,.46,.38]),
 "P2": dict(S=1, q9=0, q=[.80,.15,.05,0], t=[.90,.05,.03,.02], a=[.52,.34,.11,.03]),
 "P3": dict(S=20,q9=0, q=[0,.05,.15,.80], t=[.90,.05,.03,.02], a=[.32,.45,.19,.04]),
 "P4": dict(S=6, q9=0, q=[.10,.70,.15,.05], t=[.90,.05,.03,.02], a=[.03,.12,.43,.42]),
 "P5": dict(S=2, q9=1, q=[.80,.15,.05,0], t=[.10,.15,.70,.05], a=[.13,.48,.32,.07]),
}
tabV = {}
for p, v in P.items():
    tabV[p] = {}
    for s, w in W.items():
        raw, soft = fuse(np.array(v["t"]), np.array(v["a"]), np.array(v["q"]), w)
        k = int(raw.argmax())
        hre = v["S"] >= 20 or v["q9"] > 0
        tabV[p][s] = dict(cls=k, raw=round(float(raw.max()),4), soft=round(float(soft.max()),4), hre=hre)
# which P1-P5 phq vectors does the authors' code actually produce?
check_q = {p: vec(calculate_phq_score([0]*8+[0]).probabilities) for p in []}

# ---------- (B) Design-space scan of dilution relative to the PHQ-9 tier ----------
def phq_tier(S): return 0 if S<5 else 1 if S<10 else 2 if S<15 else 3
GAMMA = {"joy":0,"neutral":0,"surprise":0,"fear":1,"anger":1,"sadness":2,"disgust":2}
def text_vec(idx, s):
    b = [0.1]*4; b[idx] = s; b = np.array(b); return b/b.sum()
text_states = [(e, s) for e in GAMMA for s in np.round(np.arange(0.15, 0.9501, 0.05), 2)]
def audio_vec_from_index(I):
    anchors=[[.80,.15,.04,.01],[.50,.35,.12,.03],[.15,.55,.25,.05],[.05,.20,.60,.15],[.02,.08,.35,.55]]
    b=[0,.25,.45,.65,1.0]
    for k in range(4):
        if I < b[k+1] or k==3:
            return np.array(_interpolate(I, b[k], b[k+1], anchors[k], anchors[k+1]))
audio_states = [audio_vec_from_index(I) for I in np.round(np.arange(0,1.0001,0.02),2)]
PRIOR = np.array([.25,.45,.20,.10])   # server-side prior when an API call omits audio
# deployed web client: skipped/short recordings were sent as fixed neutral features
NEUTRAL = vec(get_audio_prediction(audio_features={"rms_mean":0.3,"rms_std":0.1,"zcr_mean":0.3,
          "spectral_centroid":0.4,"spectral_rolloff":0.4,"speaking_ratio":0.5})["probabilities"])

def scan(w=(.5,.3,.2), audio="present", rule1=20, floor=False):
    # rule1 = threshold of the deployed high-score rule (HS rule), not the paper's R1 (Item 9)
    """returns per-S fraction of (text,audio) configurations whose final tier < PHQ tier"""
    out = {}
    for S in range(28):
        q = vec(calculate_phq_score([0]*9 if S==0 else _answers(S)).probabilities)
        tq = phq_tier(S); n = under = over = 0
        aud = audio_states if audio=="present" else [None]
        for (e, s), a in itertools.product(text_states, aud):
            t = text_vec(GAMMA[e], s)
            if a is None:
                if audio == "prior": a = PRIOR
                elif audio == "neutral": a = NEUTRAL
            pf = vec(fuse_probabilities(dict(zip(K,t)), dict(zip(K,q)),
                     dict(zip(K,a)) if a is not None else None,
                     weights={"text":w[0], "audio":w[1], "phq":w[2]}))
            y = int(pf.argmax())
            if S >= rule1: y = 3
            if floor: y = max(y, tq)
            n += 1; under += y < tq; over += y > tq
        out[S] = dict(under=under/n, over=over/n, n=n)
    return out
def _answers(S):
    a=[0]*9; i=0
    while S>0:
        if i==8: i=0
        inc=min(3-a[i],S)
        if i<8: a[i]+=inc; S-=inc
        i+=1
        if all(x==3 for x in a[:8]) and S>0: a[8]+=S; S=0
    return a   # item 9 kept at 0 so only Rule 1 is exercised

variants = {
 "historical_baseline(HS>=20,no_R0)": scan(),
 "HS>=15": scan(rule1=15),
 "PHQ_floor_R0": scan(floor=True),
 "deployed_R0": scan(floor=True),
 "skipped_audio_neutral_features(deployed_client)": scan(audio="neutral"),
 "skipped_audio_server_prior(API)": scan(audio="prior"),
 "skipped_audio_renormalised(revised,no_R0)": scan(audio="renorm"),
 "skipped_audio_renormalised+R0(revised)": scan(audio="renorm", floor=True),
}
bands = {"0-4":range(0,5),"5-9":range(5,10),"10-14":range(10,15),"15-19":range(15,20),"20-27":range(20,28)}
summary = {v: {b: round(float(np.mean([r[S]["under"] for S in rng])),4) for b, rng in bands.items()} for v, r in variants.items()}
summary_over = {v: {b: round(float(np.mean([r[S]["over"] for S in rng])),4) for b, rng in bands.items()} for v, r in variants.items()}
config_counts = {b: sum(variants["deployed_R0"][S]["n"] for S in rng) for b, rng in bands.items()}

# ---------- (C) PHQ-only vs fused agreement for each modality subset (as deployed, no HRE) ----------
def agree(ws):
    tot=agr=0
    for S in range(28):
        q=vec(calculate_phq_score(_answers(S)).probabilities); tq=phq_tier(S)
        for (e,s),a in itertools.product(text_states, audio_states):
            t=text_vec(GAMMA[e],s)
            pf=vec(fuse_probabilities(dict(zip(K,t)), dict(zip(K,q)), dict(zip(K,a)),
                   weights={"text":ws[0], "audio":ws[1], "phq":ws[2]}))
            tot+=1; agr+= int(pf.argmax())==tq
    return round(agr/tot,4)
subsets = {"PHQ only":(0,0,1),"Text only":(1,0,0),"Audio only":(0,1,0),"Text+PHQ (.71/.29)":(.5/.7,0,.2/.7),
           "Audio+PHQ (.6/.4)":(0,.6,.4),"Text+Audio (.625/.375)":(.625,.375,0),"All (.5/.3/.2)":(.5,.3,.2)}
agreement = {k: agree(v) for k,v in subsets.items()}

json.dump(dict(methodology={"implementation":"backend/services", "uniform_synthetic_weighting":True,
               "states_per_phq_total":len(text_states)*len(audio_states), "configurations_per_band":config_counts},
               neutral_audio_vector=[round(float(x),4) for x in NEUTRAL], tableV=tabV, under=summary,
               over=summary_over, agreement=agreement, n_text_states=len(text_states),
               n_audio_states=len(audio_states)), open("results_fusion.json","w"), indent=1)
print("TABLE V (class, raw max, softened max):")
for p in tabV: print(p, {s:(d['cls'],d['raw'],d['soft']) for s,d in tabV[p].items()})
print("\nUNDER-TRIAGE vs PHQ tier (fraction of text x audio configurations):")
for v in summary: print(f"{v:22}", summary[v])
print("\nOVER-TRIAGE:")
for v in summary_over: print(f"{v:22}", summary_over[v])
print("\nAGREEMENT with PHQ tier:", agreement)
print("text states",len(text_states),"audio states",len(audio_states))
