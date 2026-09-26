/**
 * AudioFeatureExtractor
 * ---------------------
 * Extracts real acoustic features from a MediaStream using the Web Audio API.
 * Runs entirely in the browser — no server-side torch/librosa required.
 *
 * Features extracted per recording:
 *   rms_mean         — mean RMS energy (0–1): measures average loudness
 *   rms_std          — std-dev of RMS (0–1): measures energy variability (monotone = low)
 *   zcr_mean         — mean zero-crossing rate (0–1): measures voicing / breathiness
 *   spectral_centroid — normalised spectral centroid (0–1): voice brightness
 *   spectral_rolloff  — normalised 85% rolloff (0–1): high-frequency energy present
 *   speaking_ratio   — fraction of frames with RMS > silence threshold (0–1)
 */

export interface AudioFeatures {
  rms_mean: number;
  rms_std: number;
  zcr_mean: number;
  spectral_centroid: number;
  spectral_rolloff: number;
  speaking_ratio: number;
}

const SILENCE_THRESHOLD = 0.02; // frames below this RMS are treated as silence
const FFT_SIZE = 2048;
const ROLLOFF_PERCENTILE = 0.85;

export function buildAudioFeatures(
  rmsValues: number[],
  zcrValues: number[],
  centroidValues: number[],
  rolloffValues: number[],
  speakingFrames: number,
  totalFrames: number,
): AudioFeatures | null {
  // Very short captures are missing data, not neutral acoustic observations.
  if (rmsValues.length < 5 || totalFrames < 5) return null;

  const mean = (values: number[]) => values.reduce((a, b) => a + b, 0) / values.length;
  const std = (values: number[], average: number) =>
    Math.sqrt(values.reduce((a, b) => a + (b - average) ** 2, 0) / values.length);

  const rms_mean = clamp(mean(rmsValues));
  return {
    rms_mean,
    rms_std: clamp(std(rmsValues, rms_mean)),
    zcr_mean: clamp(mean(zcrValues)),
    spectral_centroid: clamp(mean(centroidValues)),
    spectral_rolloff: clamp(mean(rolloffValues)),
    speaking_ratio: clamp(speakingFrames / totalFrames),
  };
}

export class AudioFeatureExtractor {
  private audioCtx: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private source: MediaStreamAudioSourceNode | null = null;
  private rafHandle: number | null = null;

  // Per-frame accumulators
  private rmsList: number[] = [];
  private zcrList: number[] = [];
  private centroidList: number[] = [];
  private rolloffList: number[] = [];
  private speakingFrames = 0;
  private totalFrames = 0;

  start(stream: MediaStream): void {
    this.reset();

    this.audioCtx = new AudioContext();
    this.analyser = this.audioCtx.createAnalyser();
    this.analyser.fftSize = FFT_SIZE;

    this.source = this.audioCtx.createMediaStreamSource(stream);
    this.source.connect(this.analyser);

    this.collectFrame();
  }

  stop(): AudioFeatures | null {
    // Cancel animation loop
    if (this.rafHandle !== null) {
      cancelAnimationFrame(this.rafHandle);
      this.rafHandle = null;
    }

    // Disconnect and close AudioContext
    try {
      this.source?.disconnect();
      this.audioCtx?.close();
    } catch (_) {
      // ignore cleanup errors
    }

    const features = buildAudioFeatures(
      this.rmsList,
      this.zcrList,
      this.centroidList,
      this.rolloffList,
      this.speakingFrames,
      this.totalFrames,
    );

    this.reset();
    return features;
  }

  // ── Private helpers ────────────────────────────────────────────────────────

  private collectFrame = () => {
    if (!this.analyser) return;

    const bufferLength = this.analyser.fftSize;
    const freqBins = this.analyser.frequencyBinCount; // fftSize / 2

    const timeDomain = new Uint8Array(bufferLength);
    const freqDomain = new Uint8Array(freqBins);

    this.analyser.getByteTimeDomainData(timeDomain);
    this.analyser.getByteFrequencyData(freqDomain);

    // ── RMS (time domain) ──
    let sumSq = 0;
    let zeroCrossings = 0;
    let prevSign = timeDomain[0] >= 128;

    for (let i = 0; i < bufferLength; i++) {
      const sample = timeDomain[i] / 128.0 - 1.0; // normalise to [-1, 1]
      sumSq += sample * sample;
      const sign = sample >= 0;
      if (sign !== prevSign) zeroCrossings++;
      prevSign = sign;
    }

    const rms = Math.sqrt(sumSq / bufferLength);
    const zcr = zeroCrossings / bufferLength;

    // ── Spectral centroid & rolloff (frequency domain) ──
    let weightedSum = 0;
    let totalEnergy = 0;

    for (let i = 0; i < freqBins; i++) {
      const energy = freqDomain[i];
      weightedSum += i * energy;
      totalEnergy += energy;
    }

    const centroid = totalEnergy > 0 ? weightedSum / totalEnergy / freqBins : 0.4;

    let cumEnergy = 0;
    const rolloffTarget = ROLLOFF_PERCENTILE * totalEnergy;
    let rolloffBin = freqBins - 1;
    for (let i = 0; i < freqBins; i++) {
      cumEnergy += freqDomain[i];
      if (cumEnergy >= rolloffTarget) {
        rolloffBin = i;
        break;
      }
    }
    const rolloff = rolloffBin / freqBins;

    // ── Accumulate ──
    this.rmsList.push(rms);
    this.zcrList.push(zcr);
    this.centroidList.push(centroid);
    this.rolloffList.push(rolloff);
    this.totalFrames++;
    if (rms > SILENCE_THRESHOLD) this.speakingFrames++;

    this.rafHandle = requestAnimationFrame(this.collectFrame);
  };

  private reset(): void {
    this.rmsList = [];
    this.zcrList = [];
    this.centroidList = [];
    this.rolloffList = [];
    this.speakingFrames = 0;
    this.totalFrames = 0;
    this.audioCtx = null;
    this.analyser = null;
    this.source = null;
    this.rafHandle = null;
  }
}

function clamp(v: number, lo = 0, hi = 1): number {
  return Math.max(lo, Math.min(hi, isFinite(v) ? v : 0));
}
