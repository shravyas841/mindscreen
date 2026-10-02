import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { RiskResponse } from '../../types/assessment';
import { ClinicalReportModal } from './ClinicalReportModal';


const baseResult: RiskResponse = {
  risk_level: 'severe',
  confidence: 0.9,
  priority_score: 0.9,
  probabilities: { minimal: 0.1, mild: 0.1, moderate: 0.2, severe: 0.6 },
  shap_explanation: { words: [] },
  crisis_flag: true,
  resource_display_flag: true,
  phq_floor_applied: false,
  audio_present: false,
  helplines: ['Tele-MANAS: 14416', 'iCall: 9152987821'],
};

function renderReport(phqAnswers: number[], crisisTrigger: string | null = null) {
  return renderToStaticMarkup(
    <ClinicalReportModal
      isOpen
      onClose={() => undefined}
      result={{ ...baseResult, crisis_trigger: crisisTrigger }}
      phqAnswers={phqAnswers}
    />,
  );
}

describe('Assessment Report', () => {
  it('renders the real PHQ total, Item 9 attribution, priority score, resources, and prototype disclaimer', () => {
    const html = renderReport([1, 2, 0, 3, 1, 0, 2, 1, 1]);

    expect(html).toContain('Assessment Report');
    expect(html).toContain('MindScreen Mental Health Screening Summary');
    expect(html).toContain('Research Prototype — Not Clinically Validated');
    expect(html).toContain('11 / 27');
    expect(html).toContain('PHQ-9 Item 9 was endorsed');
    expect(html).toContain('Priority Score');
    expect(html).toContain('90.0%');
    expect(html).toContain('Tele-MANAS');
    expect(html).toContain('not a clinical diagnosis, medical assessment, or substitute');
    expect(html).not.toContain('Clinical Decision Support Summary');
    expect(html).not.toContain('MindScreen Clinical Screening Summary');
  });

  it('renders R2 attribution without incorrectly attributing Item 9', () => {
    const html = renderReport([0, 0, 0, 0, 0, 0, 0, 0, 0], 'kill myself');
    expect(html).toContain('Affirmative crisis language was detected');
    expect(html).not.toContain('PHQ-9 Item 9 was endorsed');
  });

  it('renders simultaneous R1 and R2 attribution', () => {
    const html = renderReport([0, 0, 0, 0, 0, 0, 0, 0, 2], 'kill myself');
    expect(html).toContain('PHQ-9 Item 9 was endorsed and affirmative crisis language was detected');
  });
});
