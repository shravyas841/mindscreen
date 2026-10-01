export interface AudioFeatures {
  rms_mean: number;
  rms_std: number;
  zcr_mean: number;
  spectral_centroid: number;
  spectral_rolloff: number;
  speaking_ratio: number;
}

export interface PHQSubmitRequest {
  answers: number[];
}

export interface PredictTextRequest {
  text: string;
}

export interface FusedPredictRequest {
  answers: number[];
  text: string;
  audio_features?: AudioFeatures | null;
  audio_base64?: string | null;
}

export interface RiskResponse {
  risk_level: 'minimal' | 'mild' | 'moderate' | 'severe';
  confidence: number;
  probabilities: {
    minimal: number;
    mild: number;
    moderate: number;
    severe: number;
  };
  shap_explanation: {
    words?: { word: string; value: number }[];
    phq_factors?: { question: string; value: number }[];
  } | null;
  audio_features?: AudioFeatures | null;
  raw_probabilities?: {
    minimal: number;
    mild: number;
    moderate: number;
    severe: number;
  } | null;
  crisis_flag: boolean;
  helplines?: string[] | null;
}
