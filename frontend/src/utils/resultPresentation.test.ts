import { describe, expect, it } from 'vitest';

import {
  ASSESSMENT_REPORT_DISCLAIMER,
  ASSESSMENT_REPORT_HEADING,
  ASSESSMENT_REPORT_STATUS,
  ASSESSMENT_REPORT_TITLE,
  calculatePhqTotal,
  createResultsNavigationState,
  formatPercentage,
  formatPriorityScore,
  getAudioUsageSummary,
  getCrisisAttribution,
  getEffectiveFusionWeights,
} from './resultPresentation';


describe('getEffectiveFusionWeights', () => {
  it('shows the deployed weights when audio is present', () => {
    const weights = getEffectiveFusionWeights(true);
    expect(weights).toEqual({ text: 50, audio: 30, phq: 20 });
    expect(getAudioUsageSummary(true)).toContain('acoustic recording');
    expect([weights.text, weights.audio, weights.phq].map(formatPercentage)).toEqual(['50.0%', '30.0%', '20.0%']);
  });

  it('shows text/PHQ renormalisation when audio is absent', () => {
    const weights = getEffectiveFusionWeights(false);
    expect(weights.text).toBeCloseTo(71.4286);
    expect(weights.audio).toBe(0);
    expect(weights.phq).toBeCloseTo(28.5714);
    expect(getAudioUsageSummary(false)).toContain('audio was not used');
    expect([weights.text, weights.audio, weights.phq].map(formatPercentage)).toEqual(['71.4%', '0.0%', '28.6%']);
  });
});

describe('assessment report presentation', () => {
  it('preserves submitted PHQ answers in result navigation and calculates their real total', () => {
    const submitted = [1, 2, 0, 3, 1, 0, 2, 1, 0];
    const state = createResultsNavigationState({ risk_level: 'moderate' }, submitted);
    submitted[0] = 3;

    expect(state.phqAnswers).toEqual([1, 2, 0, 3, 1, 0, 2, 1, 0]);
    expect(calculatePhqTotal(state.phqAnswers)).toBe(10);
  });

  it.each([
    [[0, 0, 0, 0, 0, 0, 0, 0, 1], null, 'Item 9 was endorsed', false],
    [[0, 0, 0, 0, 0, 0, 0, 0, 0], 'kill myself', 'crisis language', false],
    [[0, 0, 0, 0, 0, 0, 0, 0, 2], 'kill myself', 'Item 9 was endorsed', true],
  ])('distinguishes R1, R2, and simultaneous R1+R2', (answers, trigger, expected, both) => {
    const attribution = getCrisisAttribution(answers as number[], trigger as string | null);
    expect(attribution).toContain(expected as string);
    expect(attribution.includes('crisis language') && attribution.includes('Item 9')).toBe(both);
  });

  it('uses non-clinical research-prototype terminology and labels the score accurately', () => {
    expect(ASSESSMENT_REPORT_TITLE).toBe('Assessment Report');
    expect(ASSESSMENT_REPORT_HEADING).toContain('Mental Health Screening Summary');
    expect(ASSESSMENT_REPORT_STATUS).toBe('Research Prototype — Not Clinically Validated');
    expect(ASSESSMENT_REPORT_DISCLAIMER).toContain('not a clinical diagnosis');
    expect(ASSESSMENT_REPORT_DISCLAIMER).toContain('medical assessment');
    expect(formatPriorityScore(0.9)).toBe('90.0%');
  });
});
