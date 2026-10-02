import { describe, expect, it } from 'vitest';

import { summarizeAudioFrames } from './audioFeatures';


describe('summarizeAudioFrames', () => {
  it('marks recordings with fewer than five frames as missing', () => {
    expect(summarizeAudioFrames([0.1], [0.2], [0.3], [0.4], 1)).toBeNull();
  });

  it('returns bounded aggregate descriptors for usable recordings', () => {
    const result = summarizeAudioFrames(
      [0.1, 0.2, 0.3, 0.4, 0.5],
      [0.2, 0.2, 0.2, 0.2, 0.2],
      [0.3, 0.3, 0.3, 0.3, 0.3],
      [0.4, 0.4, 0.4, 0.4, 0.4],
      3,
    );
    expect(result).not.toBeNull();
    expect(result?.rms_mean).toBeCloseTo(0.3);
    expect(result?.speaking_ratio).toBeCloseTo(0.6);
    expect(Object.values(result ?? {}).every(value => value >= 0 && value <= 1)).toBe(true);
  });

  it('rejects mismatched frame series', () => {
    expect(summarizeAudioFrames([.1, .1, .1, .1, .1], [.2], [.3], [.4], 1)).toBeNull();
  });
});
