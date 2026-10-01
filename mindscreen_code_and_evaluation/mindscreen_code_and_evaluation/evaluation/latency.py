"""Server-side compute latency of the local (no-network) screening path."""
import time, json, tracemalloc, resource, platform, os, statistics as st, numpy as np
from orig_services.phq_service import calculate_phq_score
from orig_services.audio_service import get_audio_prediction
from orig_services.calibration_service import apply_temperature_scaling
import crisis_v1, crisis_v2
from common import load_sdcnl
texts = load_sdcnl("test").text.tolist()
feat = {"rms_mean": .3, "rms_std": .1, "zcr_mean": .2, "spectral_centroid": .4, "spectral_rolloff": .45, "speaking_ratio": .6}
phq = [1,2,1,2,1,1,0,1,0]
K = ["minimal","mild","moderate","severe"]
def pipeline(text, v=crisis_v2):
    q = calculate_phq_score(phq).probabilities
    a = get_audio_prediction(audio_features=feat)["probabilities"]
    c = v.detect_crisis_intent(text)["is_crisis"]
    t = {"minimal":.05,"mild":.05,"moderate":.05,"severe":.85} if c else {"minimal":.9,"mild":.05,"moderate":.03,"severe":.02}
    raw = {k: .5*t[k]+.3*a[k]+.2*q[k] for k in K}
    s = apply_temperature_scaling(raw, 1.2)
    return max(s, key=s.get)
def bench(fn, args_list, warm=20):
    for x in args_list[:warm]: fn(*x)
    ts = []
    for x in args_list:
        t0 = time.perf_counter(); fn(*x); ts.append((time.perf_counter()-t0)*1e3)
    ts = np.array(ts); return dict(n=len(ts), mean=float(ts.mean()), p50=float(np.percentile(ts,50)), p95=float(np.percentile(ts,95)), max=float(ts.max()))
R = {}
R["phq9_mapping"] = bench(lambda: calculate_phq_score(phq), [()]*1000)
R["acoustic_scoring"] = bench(lambda: get_audio_prediction(audio_features=feat), [()]*1000)
R["crisis_v1_per_post"] = bench(lambda t: crisis_v1.detect_crisis_intent(crisis_v2.normalise(t)), [(t,) for t in texts])
R["crisis_v2_per_post"] = bench(lambda t: crisis_v2.detect_crisis_intent(t), [(t,) for t in texts])
R["local_pipeline_v2_per_post"] = bench(lambda t: pipeline(t), [(t,) for t in texts])
tracemalloc.start(); [pipeline(t) for t in texts]; cur, peak = tracemalloc.get_traced_memory(); tracemalloc.stop()
R["tracemalloc_peak_MB"] = peak/2**20
R["maxrss_MB"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024
R["env"] = dict(python=platform.python_version(), machine=platform.machine(), cpu=open('/proc/cpuinfo').read().split('model name')[1].split('\n')[0].strip(': '), affinity=len(os.sched_getaffinity(0)))
lens = [len(t) for t in texts]; R["post_chars"] = dict(mean=float(np.mean(lens)), p95=float(np.percentile(lens,95)))
json.dump(R, open("results_latency.json","w"), indent=1)
for k,v in R.items(): print(k, v)
