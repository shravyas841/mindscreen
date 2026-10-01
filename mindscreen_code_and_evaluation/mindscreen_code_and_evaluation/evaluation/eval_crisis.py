"""Held-out evaluation of crisis-intent filters on two public corpora."""
import json, numpy as np
from scipy.stats import binomtest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from common import *
from suite import SUITE

def wilson(k, n, z=1.959964):
    if n == 0: return (float('nan'),)*2
    p = k/n; den = 1+z*z/n; c = (p+z*z/(2*n))/den; h = z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return (c-h, c+h)

def mcnemar(a, b):
    """exact McNemar on paired binary outcomes a,b (bool arrays)."""
    a = np.asarray(a, bool); b = np.asarray(b, bool)
    n01 = int((~a & b).sum()); n10 = int((a & ~b).sum())
    p = binomtest(n01, n01+n10, 0.5).pvalue if n01+n10 else 1.0
    return n01, n10, p

res = {}
tr = load_sdcnl("train")
vec = TfidfVectorizer(ngram_range=(1,2), min_df=2, sublinear_tf=True)
Xtr = vec.fit_transform(tr.text.map(normalise_fn := __import__('crisis_v2').normalise))
clf = LogisticRegression(max_iter=2000, C=1.0).fit(Xtr, tr.y)

sets = {"SDCNL-test": load_sdcnl("test"), "Twitter": load_twitter()}
for name, d in sets.items():
    out = {"n": len(d), "pos": int(d.y.sum()), "neg": int((1-d.y).sum())}
    preds = {}
    for m, f in METHODS.items():
        p = d.text.map(f).values.astype(bool); preds[m] = p
        r = metrics(d.y, p)
        r["sens_ci"] = wilson(r["tp"], r["tp"]+r["fn"]); r["spec_ci"] = wilson(r["tn"], r["tn"]+r["fp"])
        out[m] = r
    # learned baseline (trained on SDCNL train only)
    s = clf.predict_proba(vec.transform(d.text.map(normalise_fn)))[:,1]
    p = s >= 0.5; preds["tfidf_lr"] = p
    r = metrics(d.y, p); r["sens_ci"] = wilson(r["tp"], r["tp"]+r["fn"]); r["spec_ci"] = wilson(r["tn"], r["tn"]+r["fp"])
    r["auroc"] = roc_auc_score(d.y, s); out["tfidf_lr"] = r
    pos = d.y.values == 1; neg = ~pos
    out["mcnemar_v1_v2_pos"] = mcnemar(preds["v1"][pos], preds["v2"][pos])
    out["mcnemar_v1_v2_neg"] = mcnemar(~preds["v1"][neg], ~preds["v2"][neg])
    res[name] = out

# constructed suite
import crisis_v1, crisis_v2
suite = {}
for m, f in METHODS.items():
    y = np.array([s[2] for s in SUITE]); p = np.array([f(s[1]) for s in SUITE])
    orig = np.array([s[0].startswith("S") for s in SUITE])
    suite[m] = {"orig14": metrics(y[orig], p[orig]), "adv12": metrics(y[~orig], p[~orig]), "all26": metrics(y, p),
                "per_item": {s[0]: int(pp) for s, pp in zip(SUITE, p)}}
res["suite"] = suite
json.dump(res, open("results_crisis.json", "w"), indent=1, default=float)

for name in sets:
    o = res[name]; print(f"\n{name}: n={o['n']} pos={o['pos']} neg={o['neg']}")
    for m in ["naive","v1","v2","tfidf_lr"]:
        r = o[m]; print(f"  {m:9} sens={r['sens']:.3f} [{r['sens_ci'][0]:.3f},{r['sens_ci'][1]:.3f}] spec={r['spec']:.3f} [{r['spec_ci'][0]:.3f},{r['spec_ci'][1]:.3f}] ppv={r['ppv']:.3f} tp={r['tp']} fn={r['fn']} tn={r['tn']} fp={r['fp']}" + (f" auroc={r['auroc']:.3f}" if 'auroc' in r else ""))
    print("  McNemar v1 vs v2 on positives (n01 v2-only hits, n10 v1-only hits, p):", o["mcnemar_v1_v2_pos"])
    print("  McNemar v1 vs v2 on negatives (n01 v2-only correct, n10 v1-only correct, p):", o["mcnemar_v1_v2_neg"])
for m in suite: print("suite", m, {k: (v['tp'],v['fn'],v['tn'],v['fp']) for k,v in suite[m].items() if k!='per_item'})
