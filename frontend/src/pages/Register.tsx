import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { apiClient } from '../api/client';
import { Brain, User, Mail, Lock, ShieldCheck, AlertCircle, CheckCircle2 } from 'lucide-react';

export default function Register() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({ name: '', email: '', password: '', confirmPassword: '' });
  const [consent, setConsent] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const calculateStrength = (pass: string) => {
    let score = 0;
    if (pass.length > 7) score += 1;
    if (/[A-Z]/.test(pass)) score += 1;
    if (/[0-9]/.test(pass)) score += 1;
    if (/[^A-Za-z0-9]/.test(pass)) score += 1;
    return score;
  };

  const strength = calculateStrength(formData.password);
  
  const getStrengthDisplay = () => {
    if (formData.password.length === 0) return { label: 'Enter a password', color: 'bg-gray-700' };
    if (strength <= 1) return { label: 'Weak', color: 'bg-red-500', width: 'w-1/4' };
    if (strength === 2) return { label: 'Fair', color: 'bg-amber-500', width: 'w-2/4' };
    if (strength === 3) return { label: 'Good', color: 'bg-brand-teal', width: 'w-3/4' };
    return { label: 'Strong', color: 'bg-emerald-500', width: 'w-full' };
  };

  const strengthDisplay = getStrengthDisplay();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    if (!consent) {
      setError('You must agree to the research disclaimer');
      return;
    }

    setIsLoading(true);
    try {
      await apiClient.post('/auth/register', {
        name: formData.name,
        email: formData.email,
        password: formData.password
      });
      
      setSuccess(true);
      setTimeout(() => navigate('/login'), 2000);
      
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen bg-[#0D1B2A] flex items-center justify-center p-4 relative overflow-hidden">
        <div className="absolute top-[-20%] right-[-10%] w-[500px] h-[500px] bg-brand-teal/20 rounded-full blur-[150px]" />
        <div className="glass-card p-10 max-w-md w-full text-center relative z-10">
          <div className="w-16 h-16 bg-emerald-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle2 className="w-8 h-8 text-emerald-400" />
          </div>
          <h2 className="text-2xl font-bold mb-2">Registration Successful</h2>
          <p className="text-gray-400 mb-6">Welcome to MindScreen. Redirecting you to login...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0D1B2A] flex items-center justify-center p-4 relative overflow-hidden">
      {/* Background Blobs */}
      <div className="absolute top-[-20%] right-[-10%] w-[500px] h-[500px] bg-brand-teal/20 rounded-full blur-[150px] pointer-events-none" />
      <div className="absolute bottom-[-20%] left-[-10%] w-[500px] h-[500px] bg-brand-purple/20 rounded-full blur-[150px] pointer-events-none" />

      <div className="w-full max-w-md z-10 animate-in">
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-brand-teal/20 border border-brand-teal/30 mb-6">
            <Brain className="text-brand-tealL w-8 h-8" />
          </Link>
          <h1 className="text-3xl font-bold text-white mb-2">Create an Account</h1>
          <p className="text-gray-400">Join MindScreen's research platform</p>
        </div>

        <div className="glass-card p-8">
          {error && (
            <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
              <p className="text-sm text-red-200">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">Full Name</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User className="h-5 w-5 text-gray-500" />
                </div>
                <input
                  type="text"
                  required
                  className="block w-full pl-10 pr-3 py-3 border border-white/10 rounded-xl bg-white/5 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-brand-teal focus:border-transparent transition-all"
                  placeholder="John Doe"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">Email Address</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-gray-500" />
                </div>
                <input
                  type="email"
                  required
                  className="block w-full pl-10 pr-3 py-3 border border-white/10 rounded-xl bg-white/5 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-brand-teal focus:border-transparent transition-all"
                  placeholder="you@example.com"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">Password</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-500" />
                </div>
                <input
                  type="password"
                  required
                  className="block w-full pl-10 pr-3 py-3 border border-white/10 rounded-xl bg-white/5 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-brand-teal focus:border-transparent transition-all"
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                />
              </div>
              
              {formData.password.length > 0 && (
                <div className="mt-2">
                  <div className="flex justify-between items-center text-xs mb-1">
                    <span className="text-gray-400">Password strength</span>
                    <span className={strengthDisplay.color.replace('bg-', 'text-')}>{strengthDisplay.label}</span>
                  </div>
                  <div className="h-1 w-full bg-gray-700 rounded-full overflow-hidden">
                    <div className={`h-full ${strengthDisplay.color} ${strengthDisplay.width} transition-all duration-300`} />
                  </div>
                </div>
              )}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">Confirm Password</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-500" />
                </div>
                <input
                  type="password"
                  required
                  className="block w-full pl-10 pr-3 py-3 border border-white/10 rounded-xl bg-white/5 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-brand-teal focus:border-transparent transition-all"
                  placeholder="••••••••"
                  value={formData.confirmPassword}
                  onChange={(e) => setFormData({...formData, confirmPassword: e.target.value})}
                />
              </div>
            </div>

            <div className="flex items-start gap-3 mt-6 p-4 rounded-xl bg-brand-amber/5 border border-brand-amber/20">
              <div className="flex items-center h-5 mt-0.5">
                <input
                  id="consent"
                  type="checkbox"
                  checked={consent}
                  onChange={(e) => setConsent(e.target.checked)}
                  className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-brand-teal focus:ring-brand-teal focus:ring-offset-gray-900"
                />
              </div>
              <label htmlFor="consent" className="text-sm text-gray-300 cursor-pointer">
                I understand that MindScreen is a research tool, not a diagnostic medical device, and is not a substitute for professional mental healthcare.
              </label>
            </div>

            <Button
              type="submit"
              disabled={isLoading}
              className="w-full py-4 mt-6 bg-brand-teal hover:bg-brand-tealL text-white rounded-xl font-semibold shadow-lg hover:shadow-brand-teal/25 transition-all"
            >
              {isLoading ? 'Creating Account...' : 'Create Account'}
            </Button>
          </form>
        </div>

        <p className="text-center mt-8 text-gray-400">
          Already have an account?{' '}
          <Link to="/login" className="text-brand-teal hover:text-brand-tealL font-medium transition-colors">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
