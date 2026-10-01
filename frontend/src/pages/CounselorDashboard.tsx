import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { ShieldAlert, Users, Activity, Lock, Phone, AlertTriangle, Search, FileText, CheckCircle2, TrendingUp, TrendingDown } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface StudentRosterItem {
  id: string;
  name: string;
  email: string;
  risk_level: 'minimal' | 'mild' | 'moderate' | 'severe';
  confidence: number;
  last_assessment: string;
  trend: 'improving' | 'declining' | 'stable';
  crisis_flag: boolean;
  q9_flag: boolean;
}

const mockStudents: StudentRosterItem[] = [
  { id: 'STU-101', name: 'Aarav Sharma', email: 'aarav@rvitm.edu.in', risk_level: 'severe', confidence: 0.89, last_assessment: '2026-08-18', trend: 'declining', crisis_flag: true, q9_flag: true },
  { id: 'STU-102', name: 'Riya Patel', email: 'riya@rvitm.edu.in', risk_level: 'moderate', confidence: 0.78, last_assessment: '2026-08-17', trend: 'declining', crisis_flag: false, q9_flag: false },
  { id: 'STU-103', name: 'Karan Verma', email: 'karan@rvitm.edu.in', risk_level: 'mild', confidence: 0.82, last_assessment: '2026-08-16', trend: 'improving', crisis_flag: false, q9_flag: false },
  { id: 'STU-104', name: 'Ananya Gupta', email: 'ananya@rvitm.edu.in', risk_level: 'minimal', confidence: 0.94, last_assessment: '2026-08-15', trend: 'improving', crisis_flag: false, q9_flag: false },
  { id: 'STU-105', name: 'Rohan Mehta', email: 'rohan@rvitm.edu.in', risk_level: 'severe', confidence: 0.91, last_assessment: '2026-08-14', trend: 'declining', crisis_flag: true, q9_flag: true },
];

const RISK_STYLES: Record<string, { text: string; bg: string; border: string; bar: string }> = {
  minimal:  { text: 'text-emerald-400', bg: 'bg-emerald-400/10', border: 'border-emerald-400/30', bar: '#34d399' },
  mild:     { text: 'text-amber-400',   bg: 'bg-amber-400/10',   border: 'border-amber-400/30',   bar: '#fbbf24' },
  moderate: { text: 'text-orange-400',  bg: 'bg-orange-400/10',  border: 'border-orange-400/30',  bar: '#fb923c' },
  severe:   { text: 'text-red-400',     bg: 'bg-red-400/10',     border: 'border-red-500/30',     bar: '#f87171' },
};

export default function CounselorDashboard() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFilter, setSelectedFilter] = useState('All');

  const filteredStudents = mockStudents.filter((s) => {
    const matchesSearch = s.name.toLowerCase().includes(searchTerm.toLowerCase()) || s.id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = selectedFilter === 'All' || s.risk_level.toLowerCase() === selectedFilter.toLowerCase();
    return matchesSearch && matchesFilter;
  });

  const crisisStudents = mockStudents.filter((s) => s.crisis_flag);

  const riskData = [
    { name: 'Minimal', count: 18, fill: '#34d399' },
    { name: 'Mild', count: 12, fill: '#fbbf24' },
    { name: 'Moderate', count: 7, fill: '#fb923c' },
    { name: 'Severe', count: 3, fill: '#f87171' },
  ];

  return (
    <div className="space-y-8 animate-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-brand-amber/10 text-brand-amber border border-brand-amber/20 uppercase tracking-widest">
              Counselor & Faculty Oversight Portal
            </span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight">Campus Mental Health Overview</h1>
          <p className="text-gray-400 mt-1">Privacy-preserving student triaging and crisis alert system.</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" className="border-white/10 text-gray-300 hover:bg-white/5 text-sm" onClick={() => window.print()}>
            <FileText className="w-4 h-4 mr-2 text-brand-amber" />
            Print Weekly Summary
          </Button>
        </div>
      </div>

      {/* Privacy Notice Banner */}
      <div className="glass-card p-4 flex items-center gap-3 bg-brand-teal/10 border-brand-teal/30">
        <Lock className="w-5 h-5 text-brand-tealL shrink-0" />
        <p className="text-xs text-gray-300 leading-relaxed">
          <strong className="text-white">Privacy Guarantee:</strong> Student journal entries and raw voice recordings are <strong className="text-brand-tealL">strictly encrypted and private to the student</strong>. Counselors are provided only triaged risk scores, PHQ-9 trends, and emergency crisis flags.
        </p>
      </div>

      {/* Immediate Crisis Alert Panel */}
      {crisisStudents.length > 0 && (
        <div className="glass-card p-6 bg-red-500/10 border-red-500/40 relative overflow-hidden">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-red-500/20 flex items-center justify-center shrink-0">
              <ShieldAlert className="w-6 h-6 text-red-400 animate-pulse" />
            </div>
            <div className="flex-1">
              <h2 className="text-xl font-bold text-red-400 flex items-center gap-2">
                Immediate Action Required ({crisisStudents.length} Students Flagged)
              </h2>
              <p className="text-sm text-red-200 mt-1 mb-4">
                The following students triggered severe risk thresholds or self-harm indicators (PHQ-9 Question 9) in recent screenings:
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {crisisStudents.map((student) => (
                  <div key={student.id} className="bg-red-950/40 border border-red-500/30 rounded-xl p-4 flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-white">{student.name} <span className="text-xs text-gray-400">({student.id})</span></p>
                      <p className="text-xs text-red-300 mt-0.5">Flagged: {student.last_assessment} • PHQ-9 Q9 Positive</p>
                    </div>
                    <Button size="sm" className="bg-red-500 hover:bg-red-600 text-white text-xs font-bold flex items-center gap-1.5">
                      <Phone className="w-3.5 h-3.5" />
                      Contact
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Analytics Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Distribution Chart */}
        <div className="lg:col-span-2 glass-card p-6">
          <h2 className="text-lg font-semibold mb-1">Campus Risk Level Distribution</h2>
          <p className="text-xs text-gray-400 mb-6">Aggregated mental health triaging across active students</p>
          <div className="h-[220px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={riskData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" stroke="#6b7280" tick={{ fill: '#9ca3af', fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis stroke="#6b7280" tick={{ fill: '#9ca3af', fontSize: 12 }} axisLine={false} tickLine={false} />
                <Tooltip
                  cursor={{ fill: 'rgba(255,255,255,0.04)' }}
                  contentStyle={{ backgroundColor: '#0f2336', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '10px', color: '#fff', fontSize: '12px' }}
                />
                <Bar dataKey="count" radius={[6, 6, 0, 0]} maxBarSize={60}>
                  {riskData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Quick Counselor Stats */}
        <div className="glass-card p-6 space-y-4">
          <h2 className="text-lg font-semibold mb-2">Summary Metrics</h2>
          {[
            { label: 'Total Enrolled Students', val: '40', icon: Users, color: 'text-brand-tealL', bg: 'bg-brand-teal/10' },
            { label: 'Screened This Week', val: '28', icon: Activity, color: 'text-brand-amber', bg: 'bg-brand-amber/10' },
            { label: 'Follow-ups Completed', val: '24', icon: CheckCircle2, color: 'text-emerald-400', bg: 'bg-emerald-400/10' },
          ].map((stat) => (
            <div key={stat.label} className="flex items-center justify-between p-4 rounded-xl bg-white/[0.03] border border-white/[0.06]">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-xl ${stat.bg} flex items-center justify-center`}>
                  <stat.icon className={`w-5 h-5 ${stat.color}`} />
                </div>
                <span className="text-sm font-medium text-gray-300">{stat.label}</span>
              </div>
              <span className={`text-xl font-bold ${stat.color}`}>{stat.val}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Privacy-Masked Student Roster */}
      <div className="glass-card p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <h2 className="text-lg font-semibold">Privacy-Masked Student Roster</h2>

          <div className="flex flex-wrap items-center gap-3">
            {/* Search */}
            <div className="relative min-w-[200px]">
              <Search className="w-4 h-4 text-gray-500 absolute left-3 top-3" />
              <input
                type="text"
                placeholder="Search student..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-xl pl-9 pr-4 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-brand-teal"
              />
            </div>

            {/* Filter buttons */}
            <div className="flex items-center gap-1 bg-white/5 p-1 rounded-xl border border-white/10">
              {['All', 'Minimal', 'Mild', 'Moderate', 'Severe'].map((f) => (
                <button
                  key={f}
                  onClick={() => setSelectedFilter(f)}
                  className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
                    selectedFilter === f ? 'bg-brand-teal text-white' : 'text-gray-400 hover:text-white'
                  }`}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-white/10 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                <th className="py-3 px-4">Student</th>
                <th className="py-3 px-4">Latest Risk</th>
                <th className="py-3 px-4">AI Confidence</th>
                <th className="py-3 px-4">Last Assessment</th>
                <th className="py-3 px-4">Trend</th>
                <th className="py-3 px-4 text-right">Privacy Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 text-sm">
              {filteredStudents.map((s) => {
                const style = RISK_STYLES[s.risk_level] ?? RISK_STYLES.minimal;
                return (
                  <tr key={s.id} className="hover:bg-white/[0.02] transition-colors">
                    <td className="py-4 px-4">
                      <p className="font-semibold text-white">{s.name}</p>
                      <p className="text-xs text-gray-500">{s.id} • {s.email}</p>
                    </td>
                    <td className="py-4 px-4">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-bold border uppercase ${style.text} ${style.bg} ${style.border}`}>
                        {s.risk_level}
                      </span>
                    </td>
                    <td className="py-4 px-4 font-medium text-gray-300">
                      {(s.confidence * 100).toFixed(0)}%
                    </td>
                    <td className="py-4 px-4 text-gray-400 text-xs">{s.last_assessment}</td>
                    <td className="py-4 px-4">
                      {s.trend === 'improving' ? (
                        <span className="flex items-center text-xs text-emerald-400 font-medium">
                          <TrendingDown className="w-3.5 h-3.5 mr-1" /> Improving
                        </span>
                      ) : (
                        <span className="flex items-center text-xs text-red-400 font-medium">
                          <TrendingUp className="w-3.5 h-3.5 mr-1" /> Declining
                        </span>
                      )}
                    </td>
                    <td className="py-4 px-4 text-right">
                      <span className="inline-flex items-center text-xs text-gray-400 bg-white/5 px-2.5 py-1 rounded-full border border-white/10">
                        <Lock className="w-3 h-3 mr-1 text-brand-tealL" /> Text/Audio Encrypted
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
