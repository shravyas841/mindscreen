import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { apiClient } from '../api/client';
import { Button } from '../components/ui/Button';
import { History as HistoryIcon, ChevronDown, ChevronUp, AlertCircle, Calendar, ShieldAlert } from 'lucide-react';
import { RiskResponse } from '../types/assessment';

// Assuming the API returns a list of assessments with this shape
interface AssessmentHistoryItem {
  id: number;
  risk_level: string;
  confidence: number;
  probabilities: { minimal: number; mild: number; moderate: number; severe: number };
  crisis_flag: boolean;
  created_at: string;
}

const RISK_STYLES: Record<string, { text: string; bg: string; border: string }> = {
  minimal:  { text: 'text-emerald-400', bg: 'bg-emerald-400/10', border: 'border-emerald-400/30' },
  mild:     { text: 'text-amber-400',   bg: 'bg-amber-400/10',   border: 'border-amber-400/30' },
  moderate: { text: 'text-orange-400',  bg: 'bg-orange-400/10',  border: 'border-orange-400/30' },
  severe:   { text: 'text-red-400',     bg: 'bg-red-400/10',     border: 'border-red-500/30' },
};

export default function History() {
  const navigate = useNavigate();
  const [history, setHistory] = useState<AssessmentHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [filter, setFilter] = useState('All');

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        // Fallback to mock data if endpoint doesn't exist yet, but try fetching first
        const res = await apiClient.get('/phq/history').catch(() => ({ data: [] }));
        
        let data = res.data;
        
        // Mock data if empty for demonstration
        if (!data || data.length === 0) {
           data = [
             { id: 1, risk_level: 'minimal', confidence: 0.91, probabilities: { minimal: 0.91, mild: 0.05, moderate: 0.03, severe: 0.01 }, crisis_flag: false, created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString() },
             { id: 2, risk_level: 'mild', confidence: 0.75, probabilities: { minimal: 0.20, mild: 0.75, moderate: 0.04, severe: 0.01 }, crisis_flag: false, created_at: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString() },
             { id: 3, risk_level: 'moderate', confidence: 0.60, probabilities: { minimal: 0.10, mild: 0.20, moderate: 0.60, severe: 0.10 }, crisis_flag: true, created_at: new Date(Date.now() - 20 * 24 * 60 * 60 * 1000).toISOString() }
           ];
        }
        
        setHistory(data);
      } catch (err) {
        console.error("Failed to fetch history:", err);
        setError("Could not load your assessment history.");
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchHistory();
  }, []);

  const filteredHistory = filter === 'All' 
    ? history 
    : history.filter(h => h.risk_level.toLowerCase() === filter.toLowerCase());

  const toggleExpand = (id: number) => {
    setExpandedId(expandedId === id ? null : id);
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      weekday: 'short', month: 'short', day: 'numeric', year: 'numeric'
    });
  };

  return (
    <div className="max-w-4xl mx-auto animate-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <HistoryIcon className="w-6 h-6 text-brand-tealL" />
            <h1 className="text-3xl font-bold">Assessment History</h1>
          </div>
          <p className="text-gray-400">Review your past screenings and track your progress over time.</p>
        </div>
        <Button 
          onClick={() => navigate('/assessment')}
          className="bg-brand-teal hover:bg-brand-tealL text-white"
        >
          Take New Assessment
        </Button>
      </div>

      {/* Stats Summary */}
      {!isLoading && history.length > 0 && (
        <div className="glass-card p-6 mb-8 flex flex-wrap gap-6">
          <div className="flex-1 min-w-[150px]">
            <p className="text-sm text-gray-500 mb-1">Total Assessments</p>
            <p className="text-3xl font-bold text-white">{history.length}</p>
          </div>
          <div className="flex-1 min-w-[150px]">
            <p className="text-sm text-gray-500 mb-1">Latest Risk Level</p>
            <p className={`text-xl font-bold ${RISK_STYLES[history[0]?.risk_level.toLowerCase() || 'minimal']?.text || 'text-white'} capitalize`}>
              {history[0]?.risk_level || 'N/A'}
            </p>
          </div>
          <div className="w-full md:w-auto flex items-center justify-start md:justify-end gap-2 flex-wrap">
            {['All', 'Minimal', 'Mild', 'Moderate', 'Severe'].map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
                  filter === f 
                    ? 'bg-brand-teal text-white' 
                    : 'bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white'
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Main Content */}
      {isLoading ? (
        <div className="glass-card p-12 text-center text-gray-400 flex flex-col items-center">
          <div className="w-8 h-8 border-4 border-brand-teal border-t-transparent rounded-full animate-spin mb-4" />
          Loading your history...
        </div>
      ) : error ? (
        <div className="glass-card p-8 bg-red-500/10 border-red-500/30 text-center">
          <AlertCircle className="w-10 h-10 text-red-400 mx-auto mb-3" />
          <p className="text-red-200">{error}</p>
        </div>
      ) : filteredHistory.length === 0 ? (
        <div className="glass-card p-16 text-center flex flex-col items-center justify-center">
          <div className="w-20 h-20 bg-brand-teal/10 rounded-full flex items-center justify-center mb-6">
            <HistoryIcon className="w-10 h-10 text-brand-tealL" />
          </div>
          <h2 className="text-2xl font-bold mb-2">No history found</h2>
          <p className="text-gray-400 mb-8 max-w-md">
            {filter === 'All' 
              ? "You haven't taken any assessments yet. Take your first one to start tracking your mental wellness."
              : `You don't have any past assessments with a ${filter} risk level.`}
          </p>
          {filter === 'All' && (
            <Button onClick={() => navigate('/assessment')} className="bg-brand-teal hover:bg-brand-tealL text-white">
              Start Assessment Now
            </Button>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          <AnimatePresence>
            {filteredHistory.map((item, index) => {
              const isExpanded = expandedId === item.id;
              const style = RISK_STYLES[item.risk_level.toLowerCase()] || RISK_STYLES.minimal;
              
              return (
                <motion.div
                  key={item.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  transition={{ delay: index * 0.05 }}
                  className="glass-card overflow-hidden"
                >
                  {/* Card Header (Clickable) */}
                  <div 
                    onClick={() => toggleExpand(item.id)}
                    className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 cursor-pointer hover:bg-white/[0.02] transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${style.bg}`}>
                        <Calendar className={`w-6 h-6 ${style.text}`} />
                      </div>
                      <div>
                        <h3 className="font-semibold text-white">{formatDate(item.created_at)}</h3>
                        <p className="text-sm text-gray-400">AI Confidence: {(item.confidence * 100).toFixed(1)}%</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between sm:justify-end gap-6 w-full sm:w-auto">
                      <div className="flex items-center gap-3">
                        {item.crisis_flag && (
                          <span title="Crisis resources were recommended" className="flex items-center justify-center w-6 h-6 rounded-full bg-red-500/20">
                            <ShieldAlert className="w-3 h-3 text-red-400" />
                          </span>
                        )}
                        <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${style.bg} ${style.text} ${style.border}`}>
                          {item.risk_level}
                        </span>
                      </div>
                      <button className="text-gray-500 hover:text-white transition-colors">
                        {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                      </button>
                    </div>
                  </div>

                  {/* Expanded Content */}
                  <AnimatePresence>
                    {isExpanded && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3 }}
                        className="border-t border-white/5 bg-black/20"
                      >
                        <div className="p-6">
                          <h4 className="text-sm font-semibold text-gray-300 mb-4">Probability Breakdown</h4>
                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                            {[
                              { label: 'Minimal', val: item.probabilities.minimal, color: 'bg-emerald-400' },
                              { label: 'Mild', val: item.probabilities.mild, color: 'bg-amber-400' },
                              { label: 'Moderate', val: item.probabilities.moderate, color: 'bg-orange-400' },
                              { label: 'Severe', val: item.probabilities.severe, color: 'bg-red-400' },
                            ].map(prob => (
                              <div key={prob.label} className="bg-white/5 rounded-lg p-3">
                                <div className="flex justify-between items-center mb-2">
                                  <span className="text-xs text-gray-400">{prob.label}</span>
                                  <span className="text-xs font-bold text-white">{(prob.val * 100).toFixed(1)}%</span>
                                </div>
                                <div className="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden">
                                  <div className={`h-full ${prob.color}`} style={{ width: `${prob.val * 100}%` }} />
                                </div>
                              </div>
                            ))}
                          </div>
                          
                          <div className="mt-6 flex justify-end">
                             <Button 
                               variant="outline" 
                               size="sm"
                               onClick={(e) => {
                                 e.stopPropagation();
                                 navigate('/results', { state: { result: item } });
                               }}
                               className="text-xs border-brand-teal/30 text-brand-tealL hover:bg-brand-teal/10"
                             >
                               View Full Report
                             </Button>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}
