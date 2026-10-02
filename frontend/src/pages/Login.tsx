import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { login } from '../api/auth';
import { useAuthContext } from '../context/AuthContext';
import { Activity } from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const { loginUser } = useAuthContext();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      const res = await login({ email, password });
      loginUser(res.access_token, res.refresh_token);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'An error occurred');
    }
  };

  return (
    <div className="min-h-screen bg-[#0D1B2A] flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-gradient-to-br from-brand-teal/20 to-brand-navy/50 pointer-events-none" />
      
      <Card className="w-full max-w-md bg-[#1B2A3B]/80 border-white/10 z-10 backdrop-blur-xl">
        <CardHeader className="text-center pb-2">
          <div className="flex justify-center mb-4">
            <div className="bg-brand-teal/20 p-3 rounded-full">
              <Activity className="h-8 w-8 text-brand-tealL" />
            </div>
          </div>
          <CardTitle className="text-2xl font-bold text-white">
            Welcome Back
          </CardTitle>
          <p className="text-gray-400 text-sm mt-2">MindScreen Mental Health Platform</p>
        </CardHeader>
        
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4 mt-4">
            {error && <div className="p-3 bg-red-500/20 border border-red-500/50 text-red-200 rounded-md text-sm">{error}</div>}
            
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-300">Email Address</label>
              <Input 
                type="email" 
                required 
                value={email} 
                onChange={e => setEmail(e.target.value)}
                className="bg-black/20 border-white/10 text-white placeholder:text-gray-500"
                placeholder="you@example.com"
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-300">Password</label>
              <Input 
                type="password" 
                required 
                value={password} 
                onChange={e => setPassword(e.target.value)}
                className="bg-black/20 border-white/10 text-white placeholder:text-gray-500"
                placeholder="••••••••"
              />
            </div>
            
            <Button type="submit" className="w-full bg-brand-teal hover:bg-brand-tealL hover:text-brand-navy transition-all">
              Sign In
            </Button>
            
            <div className="text-center mt-4">
              <Link to="/register" className="text-brand-amber hover:text-white text-sm transition-colors">
                Don't have an account? Sign up
              </Link>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
