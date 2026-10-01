import React, { useState } from 'react';
import { useLocation, useNavigate, Navigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { RiskResponse } from '../types/assessment';
import { AlertTriangle, Phone, Home, RefreshCw, Brain, Mic, ClipboardList, CheckCircle, Info, FileText } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip as RechartsTooltip, ResponsiveContainer, Cell } from 'recharts';
import { AcousticRadarChart } from '../components/tools/AcousticRadarChart';
import { ClinicalReportModal } from '../components/tools/ClinicalReportModal';

const RISK_CONFIG: Record<string, { label: string; color: string; bg: string; border: string; barColor: string; description: string; advice: string[] }> = {
  minimal: {
    label: 'Minimal',
    color: 'text-emerald-400',
    bg: 'bg-emerald-400/10',
    border: 'border-emerald-400/40',
    barColor: '#34d399',
    description: 'Your responses suggest minimal signs of depression. Keep maintaining your well-being routines.',
    advice: ['Practice mindfulness or meditation daily', 'Maintain regular sleep schedule', 'Stay connected with friends and family', 'Exercise regularly — even a short walk helps'],
  },
  mild: {
    label: 'Mild',
    color: 'text-amber-400',
    bg: 'bg-amber-400/10',
    border: 'border-amber-400/40',
    barColor: '#fbbf24',
    description: 'Your responses suggest mild depressive symptoms. Consider implementing self-care strategies.',
    advice: ['Try journaling your thoughts and feelings', 'Practice the 4-7-8 breathing technique', 'Reduce screen time before bed', 'Consider talking to a trusted friend or counsellor'],
  },
  moderate: {
    label: 'Moderate',
    color: 'text-orange-400',
    bg: 'bg-orange-400/10',
    border: 'border-orange-400/40',
    barColor: '#fb923c',
    description: 'Your responses indicate moderate depressive symptoms. We recommend seeking professional support.',
    advice: ['Consult a mental health professional or counsellor', 'Reach out to a trusted person in your life', 'Avoid isolation — schedule social activities', 'Contact iCall: 9152987821 for support'],
  },
  severe: {
    label: 'Severe',
    color: 'text-red-400',
    bg: 'bg-red-400/10',
    border: 'border-red-500/50',
    barColor: '#f87171',
    description: 'Your responses indicate severe symptoms. Please seek professional help immediately.',
    advice: ['Contact a crisis helpline immediately', 'Reach out to a mental health professional', 'Tell a trusted person how you are feeling', 'Do not be alone — seek company and support'],
  },
};

export default function Results() {
  const location = useLocation();
  const navigate = useNavigate();
  const result = location.state?.result as RiskResponse;
  const [showReport, setShowReport] = useState(false);

  if (!result) return <Navigate to="/dashboard" replace />;

  const riskKey = result.risk_level?.toLowerCase() ?? 'minimal';
  const config = RISK_CONFIG[riskKey] ?? RISK_CONFIG.minimal;

  const probData = [
    { name: 'Minimal', value: parseFloat(((result.probabilities?.minimal ?? 0) * 100).toFixed(1)), fill: '#34d399' },
    { name: 'Mild',    value: parseFloat(((result.probabilities?.mild    ?? 0) * 100).toFixed(1)), fill: '#fbbf24' },
    { name: 'Moderate',value: parseFloat(((result.probabilities?.moderate ?? 0) * 100).toFixed(1)), fill: '#fb923c' },
    { name: 'Severe',  value: parseFloat(((result.probabilities?.severe  ?? 0) * 100).toFixed(1)), fill: '#f87171' },
  ];

  const shapWords = result.shap_explanation?.words ?? [];

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-in">

      {/* Header */}
      <div className="text-center py-6">
        <div className="flex items-center justify-center gap-2 mb-4">
          <CheckCircle className="w-6 h-6 text-brand-tealL" />
          <span className="text-brand-tealL font-medium">Assessment Complete</span>
        </div>
        <h1 className="text-4xl font-bold text-white">Your Screening Results</h1>
        <p className="text-gray-400 mt-2">Based on your PHQ-9 responses, text analysis, and voice recording</p>
      </div>

      {/* Crisis Banner — shown FIRST if severe */}
      {result.crisis_flag && (
        <div className="glass-card border-red-500/50 bg-red-500/5 p-6">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-red-500/20 flex items-center justify-center flex-shrink-0">
              <AlertTriangle className="w-6 h-6 text-red-400" />
            </div>
            <div className="flex-1">
              <h3 className="text-xl font-bold text-red-400 mb-1">Immediate Support Available</h3>
              <p className="text-gray-300 text-sm mb-4">
                Your responses suggest you may be going through a very difficult time. Please don't face this alone. Reach out now.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {(result.helplines ?? ['iCall: 9152987821', 'NIMHANS: 080-46110007', 'Vandrevala Foundation: 1860-2662-345']).map((h, i) => (
                  <div key={i} className="flex items-center gap-2 bg-red-500/15 border border-red-500/25 rounded-xl px-4 py-3">
                    <Phone className="w-4 h-4 text-red-400 flex-shrink-0" />
                    <span className="text-sm font-medium text-white">{h}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Results Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* Risk Level Card */}
        <div className={`glass-card p-8 border-2 ${config.border} flex flex-col items-center text-center`}>
          <div className={`w-20 h-20 rounded-2xl ${config.bg} border ${config.border} flex items-center justify-center mb-5`}>
            <Brain className={`w-10 h-10 ${config.color}`} />
          </div>
          <p className="text-sm text-gray-400 uppercase tracking-widest mb-2">AI Risk Assessment</p>
          <h2 className={`text-5xl font-extrabold uppercase tracking-wide mb-3 ${config.color}`}>
            {config.label}
          </h2>
          <div className="flex items-center gap-2 mb-4">
            <div className="h-2 flex-1 bg-white/10 rounded-full overflow-hidden w-32">
              <div
                className={`h-full rounded-full bg-gradient-to-r ${config.color === 'text-emerald-400' ? 'from-emerald-400 to-emerald-300' : config.color === 'text-amber-400' ? 'from-amber-400 to-amber-300' : config.color === 'text-orange-400' ? 'from-orange-400 to-orange-300' : 'from-red-400 to-red-300'}`}
                style={{ width: `${(result.confidence * 100).toFixed(0)}%` }}
              />
            </div>
            <span className="text-sm text-gray-300 font-medium">{(result.confidence * 100).toFixed(0)}% confidence</span>
          </div>
          <p className="text-sm text-gray-400 leading-relaxed">{config.description}</p>
        </div>

        {/* Probability Chart */}
        <div className="glass-card p-6">
          <h3 className="text-base font-semibold mb-1">Probability Distribution</h3>
          <p className="text-xs text-gray-500 mb-4">How the AI model scored each category</p>
          <div className="h-[200px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={probData} margin={{ top: 5, right: 10, left: -25, bottom: 5 }}>
                <XAxis dataKey="name" stroke="#4b5563" tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: '#9ca3af' }} />
                <YAxis stroke="#4b5563" tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: '#9ca3af' }} tickFormatter={(v) => `${v}%`} />
                <RechartsTooltip
                  cursor={{ fill: 'rgba(255,255,255,0.04)' }}
                  contentStyle={{ backgroundColor: '#0f2336', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '10px', color: '#fff', fontSize: '12px' }}
                  formatter={(val: number) => [`${val}%`, 'Probability']}
                />
                <Bar dataKey="value" radius={[6, 6, 0, 0]} maxBarSize={50}>
                  {probData.map((d, i) => <Cell key={i} fill={d.fill} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 grid grid-cols-2 gap-2">
            {probData.map((d) => (
              <div key={d.name} className="flex items-center justify-between text-xs bg-white/[0.03] rounded-lg px-3 py-2">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: d.fill }} />
                  <span className="text-gray-400">{d.name}</span>
                </div>
                <span className="font-semibold text-white">{d.value}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Modality Breakdown */}
      <div className="glass-card p-6">
        <div className="flex items-center gap-2 mb-4">
          <Info className="w-4 h-4 text-brand-tealL" />
          <h3 className="text-base font-semibold">How This Result Was Calculated</h3>
        </div>
        <p className="text-sm text-gray-400 mb-5">MindScreen uses a multimodal weighted fusion model combining three inputs:</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { icon: ClipboardList, label: 'PHQ-9 Questionnaire', weight: '20%', desc: 'Your 9 clinical responses mapped across the 4-tier screening severity scale', color: 'text-brand-amber', bg: 'bg-brand-amber/10' },
            { icon: Brain, label: 'DistilRoBERTa Emotion NLP', weight: '50%', desc: 'Your journal entry analysed for affective valence and distress markers via transformer inference', color: 'text-brand-tealL', bg: 'bg-brand-teal/10' },
            { icon: Mic, label: 'Acoustic Voice Analysis', weight: '30%', desc: 'Web Audio acoustic biomarkers (RMS loudness, energy variability, and spectral centroid)', color: 'text-purple-400', bg: 'bg-purple-400/10' },
          ].map((m) => {
            const Icon = m.icon;
            return (
              <div key={m.label} className="bg-white/[0.03] border border-white/[0.07] rounded-xl p-4">
                <div className="flex items-start justify-between mb-3">
                  <div className={`w-9 h-9 rounded-xl ${m.bg} flex items-center justify-center`}>
                    <Icon className={`w-4 h-4 ${m.color}`} />
                  </div>
                  <span className={`text-sm font-bold ${m.color}`}>{m.weight}</span>
                </div>
                <p className="text-sm font-medium text-white mb-1">{m.label}</p>
                <p className="text-xs text-gray-500 leading-relaxed">{m.desc}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Acoustic Somatic Biomarkers Radar */}
      {result.audio_features && (
        <div className="glass-card p-6">
          <div className="flex items-center gap-2 mb-2">
            <Mic className="w-4 h-4 text-purple-400" />
            <h3 className="text-base font-semibold">Acoustic Biomarkers — Vocal Footprint</h3>
          </div>
          <p className="text-xs text-gray-500 mb-4">
            Six-dimensional acoustic analysis extracted directly from your vocal recording via Web Audio API, mapped against healthy conversational baselines.
          </p>
          <AcousticRadarChart features={result.audio_features} />
        </div>
      )}

      {/* AI Explainability — Lexical Attribution */}
      {shapWords.length > 0 && (
        <div className="glass-card p-6">
          <div className="flex items-center gap-2 mb-2">
            <Brain className="w-4 h-4 text-brand-tealL" />
            <h3 className="text-base font-semibold">AI Explainability — Key Influential Words</h3>
          </div>
          <p className="text-xs text-gray-500 mb-4">
            The following words from your text entry had the most influence on the screening prediction. Red indicates higher distress indicators; green indicates protective/positive valence.
          </p>
          <div className="flex flex-wrap gap-2">
            {shapWords.map((w: { word: string; value: number }, i: number) => (
              <span
                key={i}
                className={`px-3 py-1.5 rounded-full text-sm font-medium border ${
                  w.value > 0
                    ? 'bg-red-400/10 text-red-400 border-red-400/20'
                    : 'bg-emerald-400/10 text-emerald-400 border-emerald-400/20'
                }`}
              >
                {w.word}
                <span className="ml-1.5 text-xs opacity-70">({w.value > 0 ? '+' : ''}{w.value.toFixed(2)})</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      <div className="glass-card p-6">
        <h3 className="text-base font-semibold mb-4">Personalised Recommendations</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {config.advice.map((tip, i) => (
            <div key={i} className="flex items-start gap-3 bg-white/[0.03] rounded-xl p-3.5 border border-white/[0.06]">
              <CheckCircle className={`w-4 h-4 flex-shrink-0 mt-0.5 ${config.color}`} />
              <p className="text-sm text-gray-300">{tip}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="flex flex-col sm:flex-row justify-center gap-4 pb-8">
        <Button variant="outline" className="border-white/20 text-white hover:bg-white/10" onClick={() => navigate('/dashboard')}>
          <Home className="w-4 h-4 mr-2" />
          Return to Dashboard
        </Button>
        <Button
          onClick={() => setShowReport(true)}
          className="bg-purple-600 hover:bg-purple-700 text-white font-semibold flex items-center gap-2"
        >
          <FileText className="w-4 h-4" />
          Clinical Summary (PDF)
        </Button>
        <Button className="bg-brand-teal hover:bg-brand-tealL text-white font-semibold" onClick={() => navigate('/assessment')}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Take Another Assessment
        </Button>
      </div>

      {/* Clinical Report Export Modal */}
      <ClinicalReportModal
        isOpen={showReport}
        onClose={() => setShowReport(false)}
        result={result}
      />
    </div>
  );
}
