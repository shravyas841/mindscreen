from pydantic import BaseModel, conlist
from typing import List, Optional, Dict, Any

class PHQSubmitRequest(BaseModel):
    answers: conlist(int, min_length=9, max_length=9) # type: ignore

class PredictTextRequest(BaseModel):
    text: str

class AudioFeatures(BaseModel):
    """Real acoustic features extracted by the browser-side Web Audio API extractor."""
    rms_mean: float          # mean RMS energy [0-1]: average loudness
    rms_std: float           # std-dev of RMS [0-1]: energy variability (low = monotone)
    zcr_mean: float          # mean zero-crossing rate [0-1]: voicing / breathiness
    spectral_centroid: float # normalised spectral centroid [0-1]: voice brightness
    spectral_rolloff: float  # normalised 85% rolloff [0-1]: high-frequency energy
    speaking_ratio: float    # fraction of frames above silence threshold [0-1]

class FusedPredictRequest(BaseModel):
    answers: conlist(int, min_length=9, max_length=9) # type: ignore
    text: str
    audio_features: Optional[AudioFeatures] = None   # real features from Web Audio API
    audio_base64: Optional[str] = None               # DEPRECATED: payload-size fallback

class RiskResponse(BaseModel):
    risk_level: str
    confidence: float
    probabilities: Dict[str, float]
    raw_probabilities: Optional[Dict[str, float]] = None
    shap_explanation: Optional[Dict[str, Any]] = None
    audio_features: Optional[Dict[str, float]] = None
    crisis_flag: bool
    helplines: Optional[List[str]] = None
