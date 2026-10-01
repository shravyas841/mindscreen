import React from 'react';
import { Button } from '../ui/Button';
import { RiskResponse } from '../../types/assessment';
import { Printer, X, ShieldAlert, CheckCircle2, FileText } from 'lucide-react';

interface ClinicalReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  result: RiskResponse;
  phqAnswers?: number[];
  journalText?: string;
}

const PHQ_ITEM_DESCRIPTIONS = [
  "Little interest or pleasure in doing things",
  "Feeling down, depressed, or hopeless",
  "Trouble falling or staying asleep, or sleeping too much",
  "Feeling tired or having little energy",
  "Poor appetite or overeating",
  "Feeling bad about yourself or that you are a failure",
  "Trouble concentrating on reading or watching TV",
  "Psychomotor slowing or restlessness",
  "Thoughts that you would be better off dead (Item 9)",
];

export const ClinicalReportModal: React.FC<ClinicalReportModalProps> = ({
  isOpen,
  onClose,
  result,
  phqAnswers,
  journalText,
}) => {
  if (!isOpen) return null;

  const handlePrint = () => {
    window.print();
  };

  const totalPHQ = phqAnswers ? phqAnswers.reduce((a, b) => a + b, 0) : null;
  const item9Endorsed = phqAnswers && phqAnswers[8] > 0;
  const now = new Date().toLocaleString();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm overflow-y-auto">
      <div className="bg-[#0D1B2A] border border-white/20 rounded-2xl w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden print:m-0 print:p-0 print:border-none print:shadow-none print:max-w-none print:max-h-none">
        
        {/* Modal Action Bar (Hidden in Print) */}
        <div className="flex items-center justify-between p-4 border-b border-white/10 bg-white/5 print:hidden">
          <div className="flex items-center gap-2 text-white font-semibold">
            <FileText className="w-5 h-5 text-brand-tealL" />
            <span>Clinical Decision Support Summary (Printable)</span>
          </div>
          <div className="flex items-center gap-2">
            <Button
              onClick={handlePrint}
              className="bg-brand-teal hover:bg-teal-600 text-white flex items-center gap-1.5 text-sm py-1.5 px-3"
            >
              <Printer className="w-4 h-4" />
              <span>Print / Save as PDF</span>
            </Button>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white p-1 rounded-lg"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Printable Report Document Body */}
        <div className="p-8 overflow-y-auto space-y-6 text-white text-sm bg-[#0D1B2A] print:text-black print:bg-white print:p-6">
          
          {/* Header */}
          <div className="border-b border-white/20 pb-4 flex justify-between items-start print:border-black">
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white print:text-black">
                MindScreen Clinical Screening Summary
              </h1>
              <p className="text-xs text-gray-400 print:text-gray-600 mt-0.5">
                Decision-Level Multimodal Screening Support Protocol (FHIR-Compatible Format)
              </p>
            </div>
            <div className="text-right text-xs text-gray-400 print:text-gray-600">
              <p>Generated: {now}</p>
              <p>Classification: Preliminary Screening</p>
            </div>
          </div>

          {/* Screening Classification Box */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-white/5 p-4 rounded-xl border border-white/10 print:border-gray-300 print:bg-gray-50">
            <div>
              <p className="text-xs text-gray-400 print:text-gray-500 uppercase">Screening Tier</p>
              <p className="text-xl font-bold uppercase text-brand-tealL print:text-black">
                {result.risk_level}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-400 print:text-gray-500 uppercase">Confidence</p>
              <p className="text-xl font-bold text-white print:text-black">
                {(result.confidence * 100).toFixed(1)}%
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-400 print:text-gray-500 uppercase">PHQ-9 Score</p>
              <p className="text-xl font-bold text-brand-amber print:text-black">
                {totalPHQ !== null ? `${totalPHQ} / 27` : 'N/A'}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-400 print:text-gray-500 uppercase">Crisis Flag (HRE)</p>
              <p className={`text-xl font-bold ${result.crisis_flag ? 'text-red-400 print:text-red-600' : 'text-emerald-400 print:text-green-600'}`}>
                {result.crisis_flag ? 'FLAGGED (Active)' : 'CLEAR'}
              </p>
            </div>
          </div>

          {/* Crisis Alert Banner if Flagged */}
          {result.crisis_flag && (
            <div className="bg-red-500/15 border border-red-500/30 p-3.5 rounded-xl flex items-start gap-3 print:border-red-400 print:bg-red-50">
              <ShieldAlert className="w-5 h-5 text-red-400 print:text-red-600 flex-shrink-0 mt-0.5" />
              <div className="text-xs">
                <p className="font-semibold text-red-300 print:text-red-700">
                  High-Risk Escalation (HRE) Protocol Active
                </p>
                <p className="text-red-200/80 print:text-red-600 mt-0.5">
                  {item9Endorsed
                    ? 'Reason: Patient endorsed suicidal ideation on PHQ-9 Item 9.'
                    : totalPHQ !== null && totalPHQ >= 20
                    ? 'Reason: Severe psychometric score burden (PHQ-9 S >= 20).'
                    : 'Reason: Verified linguistic crisis intent detected in text entry.'}
                </p>
                <p className="mt-1 text-gray-300 print:text-gray-700 font-medium">
                  Routing: Tele-MANAS (14416 / 1-800-891-4416) | iCall TISS (9152987821)
                </p>
              </div>
            </div>
          )}

          {/* Section 1: Psychometric Breakdown */}
          {phqAnswers && (
            <div>
              <h3 className="font-semibold text-sm mb-2 text-brand-tealL print:text-black">
                1. PHQ-9 Clinical Questionnaire Breakdown
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                {phqAnswers.map((ans, idx) => (
                  <div
                    key={idx}
                    className={`flex items-center justify-between p-2 rounded-lg border ${
                      idx === 8 && ans > 0
                        ? 'border-red-500/40 bg-red-500/10 print:bg-red-50 font-bold'
                        : 'border-white/10 bg-white/[0.02] print:border-gray-200'
                    }`}
                  >
                    <span className="text-gray-300 print:text-gray-700 truncate pr-2">
                      Q{idx + 1}: {PHQ_ITEM_DESCRIPTIONS[idx]}
                    </span>
                    <span
                      className={`font-mono px-2 py-0.5 rounded ${
                        idx === 8 && ans > 0 ? 'text-red-400 print:text-red-600' : 'text-gray-400 print:text-gray-600'
                      }`}
                    >
                      {ans} / 3
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Section 2: Linguistic Attribution */}
          {result.shap_explanation?.words && result.shap_explanation.words.length > 0 && (
            <div>
              <h3 className="font-semibold text-sm mb-2 text-brand-tealL print:text-black">
                2. Linguistic Feature Attribution (Influential Lexical Tokens)
              </h3>
              <div className="flex flex-wrap gap-2">
                {result.shap_explanation.words.map((w, i) => (
                  <span
                    key={i}
                    className={`text-xs px-2.5 py-1 rounded-full border ${
                      w.value > 0
                        ? 'border-red-500/30 bg-red-500/10 text-red-300 print:text-red-700'
                        : 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300 print:text-green-700'
                    }`}
                  >
                    {w.word} ({w.value > 0 ? '+' : ''}{w.value.toFixed(2)})
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Section 3: Acoustic Biomarkers */}
          {result.audio_features && (
            <div>
              <h3 className="font-semibold text-sm mb-2 text-brand-tealL print:text-black">
                3. Vocal Acoustic Biomarker Descriptors (Web Audio API)
              </h3>
              <div className="grid grid-cols-3 gap-2 text-xs font-mono">
                <div className="p-2 rounded bg-white/5 border border-white/10 print:border-gray-200">
                  RMS Loudness: {(result.audio_features.rms_mean * 100).toFixed(1)}%
                </div>
                <div className="p-2 rounded bg-white/5 border border-white/10 print:border-gray-200">
                  RMS Dynamics: {(result.audio_features.rms_std * 100).toFixed(1)}%
                </div>
                <div className="p-2 rounded bg-white/5 border border-white/10 print:border-gray-200">
                  Voicing Rate (ZCR): {(result.audio_features.zcr_mean * 100).toFixed(1)}%
                </div>
                <div className="p-2 rounded bg-white/5 border border-white/10 print:border-gray-200">
                  Spectral Centroid: {(result.audio_features.spectral_centroid * 100).toFixed(1)}%
                </div>
                <div className="p-2 rounded bg-white/5 border border-white/10 print:border-gray-200">
                  Spectral Rolloff: {(result.audio_features.spectral_rolloff * 100).toFixed(1)}%
                </div>
                <div className="p-2 rounded bg-white/5 border border-white/10 print:border-gray-200">
                  Speaking Ratio: {(result.audio_features.speaking_ratio * 100).toFixed(1)}%
                </div>
              </div>
            </div>
          )}

          {/* Section 4: Calibrated Probability Distribution */}
          <div>
            <h3 className="font-semibold text-sm mb-2 text-brand-tealL print:text-black">
              4. Calibrated Probability Distribution (Temperature-Scaled T=1.20)
            </h3>
            <div className="grid grid-cols-4 gap-2 text-center text-xs">
              {Object.entries(result.probabilities).map(([tier, prob]) => (
                <div key={tier} className="p-2 rounded bg-white/5 border border-white/10 print:border-gray-200">
                  <p className="text-gray-400 print:text-gray-500 uppercase">{tier}</p>
                  <p className="font-bold text-white print:text-black mt-0.5">{(prob * 100).toFixed(1)}%</p>
                </div>
              ))}
            </div>
          </div>

          {/* Clinician Review Sign-off Block */}
          <div className="pt-6 border-t border-white/20 print:border-black grid grid-cols-2 gap-8 text-xs text-gray-400 print:text-gray-700">
            <div>
              <p className="font-semibold text-white print:text-black mb-1">Non-Diagnostic Disclaimer:</p>
              <p className="leading-relaxed">
                MindScreen is an algorithmic screening support prototype. This summary does not constitute a clinical psychiatric diagnosis. Professional evaluation by a registered psychiatrist or psychologist is required under DSM-5 / ICD-11 guidelines.
              </p>
            </div>
            <div className="flex flex-col justify-end text-right">
              <div className="border-b border-gray-600 print:border-black w-48 ml-auto mb-2" />
              <p className="font-medium text-white print:text-black">Reviewing Clinician / Counselor</p>
              <p className="text-[11px] text-gray-500">Date & Signature</p>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};
