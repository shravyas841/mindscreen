import React, { useState } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuthContext } from '../../context/AuthContext';
import { LayoutDashboard, ClipboardList, LogOut, History, Heart, ChevronRight, Brain, MessageSquareHeart } from 'lucide-react';
import { SaathiDrawer } from '../saathi/SaathiDrawer';

export function DashboardLayout() {
  const { user, logoutUser } = useAuthContext();
  const location = useLocation();
  const navigate = useNavigate();
  const [isSaathiOpen, setIsSaathiOpen] = useState(false);

  const handleLogout = () => {
    logoutUser();
    navigate('/login');
  };

  const navItems = [
    { name: 'Dashboard',         path: '/dashboard',  icon: LayoutDashboard },
    { name: 'Saathi Companion', path: '/saathi',     icon: MessageSquareHeart },
    { name: 'New Assessment',    path: '/assessment', icon: ClipboardList },
    { name: 'History',           path: '/history',    icon: History },
    { name: 'Mood Tracker',      path: '/mood',       icon: Heart },
  ];

  return (
    <div className="flex h-screen bg-[#1D1722] text-[#E6E2EB] overflow-hidden relative font-sans">
      
      {/* Ambient Twilight Background Glows */}
      <div 
        className="fixed inset-0 pointer-events-none z-0"
        style={{
          background: `
            radial-gradient(ellipse 70% 50% at 10% 10%, rgba(198, 172, 214, 0.05) 0%, transparent 60%),
            radial-gradient(ellipse 60% 50% at 90% 80%, rgba(142, 168, 195, 0.05) 0%, transparent 60%)
          `,
        }}
      />

      {/* ── SLEEK EDITORIAL SIDEBAR ── */}
      <aside 
        className="w-60 flex-shrink-0 bg-[#241D2B]/75 border-r border-[#81B29A]/15 flex flex-col relative z-20 backdrop-blur-xl"
      >
        {/* Logo */}
        <div className="p-5 border-b border-[#81B29A]/15">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-8 h-8 rounded-xl bg-[#81B29A]/15 border border-[#81B29A]/30 flex items-center justify-center transition-transform group-hover:scale-105">
              <Brain className="text-[#94D2BD] w-4 h-4" />
            </div>
            <div>
              <h1 className="font-serif-title text-xl font-bold tracking-wider text-[#FFE8C2] leading-none">MindScreen</h1>
              <p className="text-[9px] text-[#94D2BD] uppercase tracking-widest mt-1">
                Research Prototype
              </p>
            </div>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group text-sm ${
                  isActive
                    ? 'bg-[#81B29A]/15 text-[#94D2BD] border border-[#81B29A]/30 font-semibold shadow-xs'
                    : 'text-[#E8B4B8]/70 hover:text-[#FFE8C2] hover:bg-white/[0.04]'
                }`}
              >
                <div className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 transition-colors ${
                  isActive
                    ? 'bg-[#81B29A]/20 text-[#94D2BD]'
                    : 'bg-white/5 text-[#E8B4B8]/60 group-hover:bg-white/10 group-hover:text-[#FFE8C2]'
                }`}>
                  <Icon className="w-4 h-4" />
                </div>
                <span className="font-medium">{item.name}</span>
                {isActive && (
                  <ChevronRight className="w-3.5 h-3.5 ml-auto text-[#94D2BD] flex-shrink-0" />
                )}
              </Link>
            );
          })}
        </nav>

        {/* User Footer */}
        <div className="p-3 border-t border-[#81B29A]/15">
          <div className="flex items-center gap-2.5 px-3 py-2.5 rounded-xl bg-white/[0.03] mb-1.5 border border-white/5">
            <div className="w-7 h-7 rounded-full bg-gradient-to-br from-[#81B29A] via-[#94D2BD] to-[#FFE8C2] flex items-center justify-center text-slate-950 font-bold text-xs flex-shrink-0">
              {user?.email?.charAt(0).toUpperCase() || 'S'}
            </div>
            <div className="min-w-0">
              <p className="text-xs font-semibold truncate text-[#FFE8C2]">{user?.email?.split('@')[0] || 'User'}</p>
              <p className="text-[10px] text-[#E8B4B8]/50 truncate">{user?.email || 'user@mindscreen.local'}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-[#E8B4B8]/60 hover:text-rose-300 hover:bg-rose-500/10 transition-all text-xs"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content Viewport */}
      <main className="flex-1 overflow-y-auto overflow-x-hidden relative z-10">
        <div className="p-6 sm:p-8 max-w-6xl mx-auto min-h-full">
          <Outlet />
        </div>
      </main>

      {/* Floating Button: 🌿 Talk to Saathi */}
      <button
        onClick={() => setIsSaathiOpen(true)}
        className="fixed bottom-6 right-6 z-50 px-4 py-2.5 rounded-full bg-[#81B29A] hover:bg-[#94D2BD] text-slate-950 font-bold text-xs shadow-[0_0_20px_rgba(129,178,154,0.4)] flex items-center gap-2 transition-all hover:scale-105 cursor-pointer"
      >
        <span>🌿</span>
        <span>Talk to Saathi</span>
      </button>

      {/* Saathi Companion Drawer */}
      <SaathiDrawer isOpen={isSaathiOpen} onClose={() => setIsSaathiOpen(false)} />

    </div>
  );
}
