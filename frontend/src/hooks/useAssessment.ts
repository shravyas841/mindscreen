import { useMutation } from '@tanstack/react-query';
import { predictFused } from '../api/assessment';
import { PHQSubmitRequest, PredictTextRequest, AudioFeatures } from '../types/assessment';

export const usePredictFused = () => {
  return useMutation({
    mutationFn: ({
      phq,
      text,
      audioFeatures,
      audioBase64,
    }: {
      phq: PHQSubmitRequest;
      text: PredictTextRequest;
      audioFeatures?: AudioFeatures | null;
      audioBase64?: string | null;
    }) => predictFused(phq, text, audioFeatures, audioBase64),
  });
};
