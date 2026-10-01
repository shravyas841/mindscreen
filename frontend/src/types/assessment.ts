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
}

export interface RiskResponse {
  risk_level: 'minimal' | 'mild' | 'moderate' | 'severe';
  confidence: number;
  priority_score: number;
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
  resource_display_flag: boolean;
  phq_floor_applied: boolean;
  audio_present?: boolean | null;
  text_inference_source?: string | null;
  helplines?: string[] | null;
}
