import { apiClient } from './client';
import { PHQSubmitRequest, PredictTextRequest, RiskResponse, AudioFeatures } from '../types/assessment';

export const predictFused = async (
  phq: PHQSubmitRequest,
  text: PredictTextRequest,
  audioFeatures?: AudioFeatures | null,
): Promise<RiskResponse> => {
  const response = await apiClient.post('/api/predict/fused', {
    answers: phq.answers,
    text: text.text,
    audio_features: audioFeatures || null,
  });
  return response.data;
};
