import React, { useCallback, useEffect, useState } from 'react';
import { Activity, AlertCircle, Heart, Phone } from 'lucide-react';
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { apiClient } from '../api/client';
import { Button } from '../components/ui/Button';


const MOODS = [
  { score: 5, emoji: '😊', label: 'Great' },
  { score: 4, emoji: '🙂', label: 'Good' },
  { score: 3, emoji: '😐', label: 'Okay' },
  { score: 2, emoji: '😔', label: 'Low' },
  { score: 1, emoji: '😢', label: 'Terrible' },
];

interface MoodLog {
  id: number;
  date: string;
  mood_score: number;
  notes?: string | null;
}

export default function MoodTracker() {
  const [selectedMood, setSelectedMood] = useState<number | null>(null);
  const [notes, setNotes] = useState('');
  const [logs, setLogs] = useState<MoodLog[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const loadTrend = useCallback(async () => {
    try {
      const response = await apiClient.get('/api/mood/trend');
      setLogs(response.data ?? []);
    } catch {
      setError('Could not load the mood history.');
    }
  }, []);

  useEffect(() => { void loadTrend(); }, [loadTrend]);

  const handleLogMood = async () => {
    if (selectedMood === null) return;
    setIsSubmitting(true);
    setError('');
    try {
      await apiClient.post('/api/mood/log', { mood_score: selectedMood, notes: notes || null });
      setSelectedMood(null);
      setNotes('');
      await loadTrend();
    } catch {
      setError('Failed to save the mood entry.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const chartData = logs.slice(-14).map(log => ({
    ...log,
    label: new Date(`${log.date}T00:00:00`).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
  }));

  return (
    <div className="max-w-5xl mx-auto animate-in space-y-8">
      <div>
        <div className="flex items-center gap-2 mb-2">
          <Heart className="w-6 h-6 text-brand-coral" />
          <h1 className="text-3xl font-bold">Daily Mood Tracker</h1>
        </div>
        <p className="text-gray-400">Record a 1–5 mood score and an optional note.</p>
      </div>

      {error && <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-200 flex gap-2"><AlertCircle className="w-4 h-4" />{error}</div>}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="glass-card p-8">
          <h2 className="text-xl font-bold mb-6 text-center">How are you feeling today?</h2>
          <div className="flex justify-between mb-8">
            {MOODS.map(mood => (
              <button key={mood.score} onClick={() => setSelectedMood(mood.score)} className="flex flex-col items-center gap-2">
                <span className={`text-4xl rounded-full p-2 ${selectedMood === mood.score ? 'bg-brand-teal/25 ring-2 ring-brand-teal' : 'bg-white/5'}`}>{mood.emoji}</span>
                <span className="text-xs text-gray-300">{mood.label}</span>
              </button>
            ))}
          </div>
          <textarea value={notes} onChange={event => setNotes(event.target.value)} maxLength={2000} placeholder="Optional note" className="w-full bg-black/20 border border-white/10 rounded-xl p-4 h-28 mb-5" />
          <Button onClick={handleLogMood} disabled={selectedMood === null || isSubmitting} className="w-full bg-brand-teal">
            {isSubmitting ? 'Saving…' : 'Save mood entry'}
          </Button>
        </div>

        <div className="glass-card p-6">
          <div className="flex items-center gap-2 mb-6"><Activity className="w-5 h-5 text-brand-tealL" /><h2 className="text-lg font-semibold">Recent trend</h2></div>
          {chartData.length === 0 ? (
            <p className="text-gray-400 text-sm">No mood entries have been saved yet.</p>
          ) : (
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 20, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                  <XAxis dataKey="label" tick={{ fill: '#9ca3af', fontSize: 11 }} />
                  <YAxis domain={[1, 5]} ticks={[1,2,3,4,5]} />
                  <Tooltip formatter={(value: number) => [value, 'Mood']} />
                  <Line type="monotone" dataKey="mood_score" stroke="#0A9396" strokeWidth={3} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>

      <div className="glass-card p-5 border-red-500/25 flex gap-3">
        <Phone className="w-5 h-5 text-red-400 shrink-0" />
        <p className="text-sm text-gray-300">Need support? Tele-MANAS: 14416 or 1-800-891-4416 (free, 24/7). iCall (TISS): 9152987821.</p>
      </div>
    </div>
  );
}
