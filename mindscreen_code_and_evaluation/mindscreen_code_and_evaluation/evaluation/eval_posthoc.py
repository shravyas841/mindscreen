"""Post hoc analyses requested in verification (run after the main evaluation)."""
import json, re, numpy as np
from common import *
from eval_crisis import wilson, mcnemar
import crisis_v1, crisis_v2, crisis_v2_1
from suite import SUITE

def v1_raw(t): return crisis_v1.detect_crisis_intent(t)["is_crisis"]          # no shared normalisation
def v21(t): return crisis_v2_1.detect_crisis_intent(t)["is_crisis"]
def abl(t): return crisis_v2_1.detect_v2scope_v1vocab(t)["is_crisis"]
M = {"v1_raw_input": v1_raw, "v2_scope_v1_vocab": abl, "v2.1_selfharm": v21}
out = {}
for name, d in {"SDCNL-test": load_sdcnl("test"), "Twitter": load_twitter()}.items():
    o = {}
    pv1 = d.text.map(v1).values.astype(bool); pv2 = d.text.map(v2).values.astype(bool)
    for m, f in M.items():
        p = d.text.map(f).values.astype(bool); r = metrics(d.y, p)
        r["sens_ci"] = wilson(r["tp"], r["tp"]+r["fn"]); r["spec_ci"] = wilson(r["tn"], r["tn"]+r["fp"]); o[m] = r
    pos = d.y.values == 1
    # v1 miss breakdown (shared normalisation, as in the main table)
    c = {"detected":0,"idiom":0,"negation":0,"third_party":0,"no_trigger":0}
    for t in d.text[pos]:
        r = crisis_v1.detect_crisis_intent(crisis_v2.normalise(t))
        k = "detected" if r["is_crisis"] else "idiom" if r["colloquial"] else "negation" if r["negated"] else "third_party" if r["third_party"] else "no_trigger"
        c[k] += 1
    o["v1_miss_breakdown"] = c
    lex = lambda t: any(re.search(p, crisis_v2.normalise(t)) for p, _ in crisis_v2.EXPLICIT)
    o["v2_lexicon_ceiling_pos"] = float(d.text[pos].map(lex).mean())
    # attribution of v2's extra hits over v1
    v1lex = lambda t: any(re.search(p, crisis_v2.normalise(t)) for p in NAIVE_PATTERNS)
    extra = pos & pv2 & ~pv1
    o["v2_extra_hits_over_v1"] = int(extra.sum())
    o["v2_extra_hits_without_any_v1_trigger"] = int(sum(1 for t in d.text[extra] if not v1lex(t)))
    o["mcnemar_v1_vs_v2scope_v1vocab_pos"] = mcnemar(pv1[pos], d.text.map(abl).values.astype(bool)[pos])
    out[name] = o
y = np.array([s[2] for s in SUITE])
out["suite_v2.1_correct"] = int(sum(int(v21(s[1])) == s[2] for s in SUITE))
out["suite_v2scope_v1vocab_correct"] = int(sum(int(abl(s[1])) == s[2] for s in SUITE))
json.dump(out, open("results_posthoc.json", "w"), indent=1, default=float)
for k, v in out.items():
    if isinstance(v, dict):
        print(k)
        for kk, vv in v.items():
            if isinstance(vv, dict) and "sens" in vv:
                print(f"  {kk:18} sens={vv['sens']:.3f} [{vv['sens_ci'][0]:.3f},{vv['sens_ci'][1]:.3f}] spec={vv['spec']:.3f} [{vv['spec_ci'][0]:.3f},{vv['spec_ci'][1]:.3f}] ppv={vv['ppv']:.3f}")
            else: print(f"  {kk}: {vv}")
    else: print(k, v)
