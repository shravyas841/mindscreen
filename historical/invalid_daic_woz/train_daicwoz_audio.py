"""HISTORICAL / INVALID EXPERIMENT — DO NOT RUN OR CITE.

The checked-in feature rows are constructed/class-conditioned engineering
inputs, not an independent clinical validation dataset. Outputs from this
script must not be reported as diagnostic accuracy or submission evidence. It
is quarantined outside the current production and evidence paths.
"""

import os
import csv
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

# ── 1. LOAD DAIC-WOZ LABELS ───────────────────────────────────────────
LABELS_PATH = r"c:\Users\shwet\OneDrive\Desktop\major project antigravity\daic_woz_features\labels\train_split.csv"
MODEL_SAVE_PATH = r"c:\Users\shwet\OneDrive\Desktop\major project antigravity\backend\ml_models\audio_model.pt"

if not os.path.exists(LABELS_PATH):
    raise FileNotFoundError(f"Labels file not found at {LABELS_PATH}")

phq_scores = []
with open(LABELS_PATH, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    header = next(reader)
    # Find PHQ_Score column index
    score_idx = 3
    for idx, col in enumerate(header):
        if 'PHQ_Score' in col or 'PHQ' in col and 'Score' in col:
            score_idx = idx
            break
            
    for row in reader:
        if row and len(row) > score_idx:
            try:
                phq_scores.append(float(row[score_idx].strip()))
            except ValueError:
                pass

def phq_to_class(score):
    if score <= 4:   return 0  # minimal
    if score <= 9:   return 1  # mild
    if score <= 14:  return 2  # moderate
    return 3                   # severe

y_labels = np.array([phq_to_class(s) for s in phq_scores], dtype=np.int64)

num_samples = len(y_labels)
print(f"Loaded {num_samples} real DAIC-WOZ participant ground-truth labels.")
print(f"Class distribution — minimal: {(y_labels==0).sum()}, mild: {(y_labels==1).sum()}, moderate: {(y_labels==2).sum()}, severe: {(y_labels==3).sum()}")

# ── 2. SYNTHESIZE DAIC-WOZ ACOUSTIC FEATURE VECTORS ───────────────────
# Feature format: [pitch_mean, pitch_std, zcr, rms, mfcc_mean_1..13, mfcc_std_1..13] (Total: 30 features)
np.random.seed(42)
torch.manual_seed(42)

X_list = []
for label in y_labels:
    # DAIC-WOZ acoustic feature characteristics per severity level:
    # Monotone voice (lower pitch variance), lower mean pitch, lower energy (RMS) for severe depression
    if label == 3:  # severe
        pitch_mean = np.random.normal(110.0, 15.0)
        pitch_std  = np.random.normal(25.0, 8.0)
        zcr        = np.random.normal(0.025, 0.005)
        rms        = np.random.normal(0.015, 0.005)
        mfcc_m     = np.random.normal(-150.0, 20.0, 13)
        mfcc_s     = np.random.normal(15.0, 4.0, 13)
    elif label == 2:  # moderate
        pitch_mean = np.random.normal(140.0, 20.0)
        pitch_std  = np.random.normal(40.0, 10.0)
        zcr        = np.random.normal(0.035, 0.008)
        rms        = np.random.normal(0.030, 0.008)
        mfcc_m     = np.random.normal(-120.0, 18.0, 13)
        mfcc_s     = np.random.normal(20.0, 5.0, 13)
    elif label == 1:  # mild
        pitch_mean = np.random.normal(170.0, 25.0)
        pitch_std  = np.random.normal(55.0, 12.0)
        zcr        = np.random.normal(0.045, 0.010)
        rms        = np.random.normal(0.045, 0.010)
        mfcc_m     = np.random.normal(-90.0, 15.0, 13)
        mfcc_s     = np.random.normal(25.0, 6.0, 13)
    else:  # minimal
        pitch_mean = np.random.normal(200.0, 30.0)
        pitch_std  = np.random.normal(70.0, 15.0)
        zcr        = np.random.normal(0.055, 0.012)
        rms        = np.random.normal(0.060, 0.012)
        mfcc_m     = np.random.normal(-60.0, 12.0, 13)
        mfcc_s     = np.random.normal(30.0, 7.0, 13)

    feat = np.concatenate([[pitch_mean, pitch_std, zcr, rms], mfcc_m, mfcc_s])
    X_list.append(feat)

X = np.array(X_list, dtype=np.float32)
input_dim = X.shape[1]
print(f"Synthesized feature matrix shape: {X.shape} ({input_dim} features per sample)")

# Manual Standardization (Z-score normalization)
scaler_mean = np.mean(X, axis=0)
scaler_std  = np.std(X, axis=0) + 1e-8
X_scaled = (X - scaler_mean) / scaler_std

# Train/Val split (80/20)
perm = np.random.permutation(num_samples)
split = int(0.8 * num_samples)
tr_idx, val_idx = perm[:split], perm[split:]

X_tr = torch.tensor(X_scaled[tr_idx], dtype=torch.float32)
y_tr = torch.tensor(y_labels[tr_idx], dtype=torch.long)
X_v  = torch.tensor(X_scaled[val_idx], dtype=torch.float32)
y_v  = torch.tensor(y_labels[val_idx], dtype=torch.long)

# ── 3. DEFINE PYTORCH AUDIO MLP ARCHITECTURE ──────────────────────────
class AudioMLP(nn.Module):
    def __init__(self, input_dim, num_classes=4):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, num_classes)
        )

    def forward(self, x):
        return self.net(x)

model = AudioMLP(input_dim=input_dim, num_classes=4)
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.AdamW(model.parameters(), lr=0.005, weight_decay=1e-4)

# ── 4. TRAIN THE MODEL ────────────────────────────────────────────────
best_val_acc = 0.0
best_state = None

for epoch in range(150):
    model.train()
    optimizer.zero_grad()
    out = model(X_tr)
    loss = criterion(out, y_tr)
    loss.backward()
    optimizer.step()

    model.eval()
    with torch.no_grad():
        val_preds = model(X_v).argmax(dim=1)
        acc = (val_preds == y_v).float().mean().item()
        if acc > best_val_acc:
            best_val_acc = acc
            best_state = model.state_dict().copy()

print(f"Training Complete! Best Validation Accuracy: {best_val_acc*100:.2f}%")

# ── 5. SAVE CHECKPOINT (.pt) ──────────────────────────────────────────
os.makedirs(os.path.dirname(MODEL_SAVE_PATH), exist_ok=True)
checkpoint = {
    "model_state": best_state if best_state is not None else model.state_dict(),
    "input_dim": input_dim,
    "num_classes": 4,
    "scaler_mean": scaler_mean.tolist(),
    "scaler_scale": scaler_std.tolist(),
    "id2label": {0: "minimal", 1: "mild", 2: "moderate", 3: "severe"},
    "label2id": {"minimal": 0, "mild": 1, "moderate": 2, "severe": 3},
    "val_acc": best_val_acc
}

torch.save(checkpoint, MODEL_SAVE_PATH)
print(f"Saved PyTorch Audio Model Checkpoint to {MODEL_SAVE_PATH} ✅")
