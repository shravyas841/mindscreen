import re, pandas as pd, numpy as np
import crisis_v1, crisis_v2
NAIVE_PATTERNS = crisis_v1.EXPLICIT_SUICIDAL_PHRASES + [rf"\b{re.escape(t)}\b" for t in crisis_v1.CRISIS_TOKENS]
def naive(text):
    t = crisis_v2.normalise(text)
    return any(re.search(p, t) for p in NAIVE_PATTERNS)
def v1(text):
    return crisis_v1.detect_crisis_intent(crisis_v2.normalise(text))["is_crisis"]
def v2(text):
    return crisis_v2.detect_crisis_intent(text)["is_crisis"]
METHODS = {"naive": naive, "v1": v1, "v2": v2}
def load_sdcnl(split):
    f = {"train": "training-set.csv", "test": "testing-set.csv"}[split]
    d = pd.read_csv(f"../data/SDCNL/data/{f}")
    d["text"] = d.title.fillna("") + ". " + d.selftext.fillna("")
    return d[["text"]].assign(y=d.is_suicide.astype(int))
def load_twitter():
    d = pd.read_csv("../data/twitter-suicidal-intention-dataset/twitter-suicidal_data.csv")
    d = d.dropna().drop_duplicates(subset="tweet")
    return pd.DataFrame({"text": d.tweet.astype(str), "y": d.intention.astype(int)})
def metrics(y, p):
    y = np.asarray(y); p = np.asarray(p).astype(int)
    tp = int(((p==1)&(y==1)).sum()); fn = int(((p==0)&(y==1)).sum())
    tn = int(((p==0)&(y==0)).sum()); fp = int(((p==1)&(y==0)).sum())
    return dict(tp=tp, fn=fn, tn=tn, fp=fp,
        sens=tp/(tp+fn) if tp+fn else float('nan'), spec=tn/(tn+fp) if tn+fp else float('nan'),
        ppv=tp/(tp+fp) if tp+fp else float('nan'))
