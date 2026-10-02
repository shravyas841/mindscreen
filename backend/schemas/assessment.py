from pydantic import BaseModel, Field, conint, conlist
from typing import List, Optional, Dict, Any

class PHQSubmitRequest(BaseModel):
    answers: conlist(conint(ge=0, le=3), min_length=9, max_length=9) # type: ignore

class PredictTextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10000)

class AudioFeatures(BaseModel):
    """Real acoustic features extracted by the browser-side Web Audio API extractor."""
    rms_mean: float = Field(ge=0, le=1)
    rms_std: float = Field(ge=0, le=1)
    zcr_mean: float = Field(ge=0, le=1)
    spectral_centroid: float = Field(ge=0, le=1)
    spectral_rolloff: float = Field(ge=0, le=1)
    speaking_ratio: float = Field(ge=0, le=1)

class FusedPredictRequest(BaseModel):
    answers: conlist(conint(ge=0, le=3), min_length=9, max_length=9) # type: ignore
    text: str = Field(min_length=1, max_length=10000)
    audio_features: Optional[AudioFeatures] = None   # real features from Web Audio API

class RiskResponse(BaseModel):
    risk_level: str
    confidence: float
    priority_score: float
    probabilities: Dict[str, float]
    raw_probabilities: Optional[Dict[str, float]] = None
    shap_explanation: Optional[Dict[str, Any]] = None
    audio_features: Optional[Dict[str, float]] = None
    crisis_flag: bool
    resource_display_flag: bool
    phq_floor_applied: bool = False
    audio_present: Optional[bool] = None
    crisis_trigger: Optional[str] = None
    text_inference_source: Optional[str] = None
    helplines: Optional[List[str]] = None
