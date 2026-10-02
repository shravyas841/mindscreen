import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, ClipboardList, Heart, MessageSquareHeart, ShieldAlert, Wind } from 'lucide-react';

import { Button } from '../components/ui/Button';
import { GuidedBreathingModal } from '../components/tools/GuidedBreathingModal';
import { useAuthContext } from '../context/AuthContext';


export default function Dashboard() {
  const { user } = useAuthContext();
  const navigate = useNavigate();
  const [isBreathingOpen, setIsBreathingOpen] = useState(false);

  const actions = [
    {
      title: 'Start a screening',
      description: 'Complete PHQ-9, a journal entry, and an optional acoustic check-in.',
      path: '/assessment',
      icon: ClipboardList,
    },
    {
      title: 'View your history',
      description: 'Review screening records saved for this account.',
      path: '/history',
      icon: ArrowRight,
    },
    {
      title: 'Log your mood',
      description: 'Record a short daily mood score and optional note.',
      path: '/mood',
      icon: Heart,
    },
    {
      title: 'Talk to Saathi',
      description: 'Use the experimental wellbeing companion with crisis-language routing.',
      path: '/saathi',
      icon: MessageSquareHeart,
    },
  ];

  return (
    <div className="space-y-8 animate-in">
      <GuidedBreathingModal isOpen={isBreathingOpen} onClose={() => setIsBreathingOpen(false)} />

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#81B29A]/15 pb-6">
        <div>
          <h1 className="font-serif-title text-3xl sm:text-4xl text-[#FFE8C2]">
            Welcome, {user?.email?.split('@')[0] || 'User'}
          </h1>
          <p className="text-sm text-[#F0C0C6]/80 mt-2">Choose a research-prototype tool below.</p>
        </div>
        <Button onClick={() => setIsBreathingOpen(true)} className="bg-[#241D2B] text-[#94D2BD] border border-[#81B29A]/30">
          <Wind className="w-4 h-4 mr-2" /> Guided breathing
        </Button>
      </div>

      <div className="glass-card p-5 border-amber-400/25 bg-amber-400/5 flex gap-3">
        <ShieldAlert className="w-5 h-5 text-amber-300 shrink-0 mt-0.5" />
        <p className="text-sm text-gray-300">
          MindScreen is not clinically validated and does not diagnose depression. If you may be in immediate danger,
          contact local emergency services or Tele-MANAS at 14416.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {actions.map(({ title, description, path, icon: Icon }) => (
          <button
            key={path}
            onClick={() => navigate(path)}
            className="glass-card p-6 text-left border-[#81B29A]/20 hover:border-[#81B29A]/45 transition-all group"
          >
            <Icon className="w-6 h-6 text-[#94D2BD] mb-4" />
            <h2 className="text-xl text-[#FFE8C2] font-semibold">{title}</h2>
            <p className="text-sm text-[#F0C0C6]/75 mt-2">{description}</p>
          </button>
        ))}
      </div>
    </div>
  );
}
