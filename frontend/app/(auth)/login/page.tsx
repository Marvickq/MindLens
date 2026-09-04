'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const router = useRouter();
  const [isLogin, setIsLogin] = useState(true);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('sarah.chen@greenwood.edu');
  const [password, setPassword] = useState('MindLens2024!');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const endpoint = isLogin ? '/api/v1/auth/login' : '/api/v1/auth/signup';
      const body = isLogin ? { email, password } : { name, email, password };
      
      const res = await fetch(`http://localhost:8000${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Authentication failed');
      }
      
      const data = await res.json();
      localStorage.setItem('MindLens_token', data.access_token);
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-[#F7F5EF]">
      <div className="glass-card w-full max-w-md p-8 rounded-2xl ambient-shadow border border-[#D9DDD9]">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-[#013f53] mb-2">MindLens</h1>
          <p className="text-sm text-[#41484c]">Counselor Portal Login</p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-300 text-red-700 text-xs rounded-lg">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          {!isLogin && (
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-[#013f53] mb-2">
                Full Name
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="w-full px-4 py-3 rounded-lg border border-[#c1c7cc] bg-white text-[#1a1c1d] focus:outline-none focus:border-[#24566b]"
              />
            </div>
          )}

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-[#013f53] mb-2">
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-4 py-3 rounded-lg border border-[#c1c7cc] bg-white text-[#1a1c1d] focus:outline-none focus:border-[#24566b]"
            />
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-[#013f53] mb-2">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-4 py-3 rounded-lg border border-[#c1c7cc] bg-white text-[#1a1c1d] focus:outline-none focus:border-[#24566b]"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full btn-primary py-3 font-semibold text-base mt-2"
          >
            {loading ? 'Authenticating...' : (isLogin ? 'Sign In' : 'Sign Up')}
          </button>
        </form>

        <div className="mt-6 text-center text-xs text-[#71787d]">
          <p className="mb-2">
            {isLogin ? "Don't have an account?" : "Already have an account?"}{' '}
            <button
              onClick={() => {
                setIsLogin(!isLogin);
                if (isLogin) {
                  setName('');
                  setEmail('');
                  setPassword('');
                } else {
                  setEmail('sarah.chen@greenwood.edu');
                  setPassword('MindLens2024!');
                }
              }}
              type="button"
              className="text-[#24566b] font-bold hover:underline"
            >
              {isLogin ? 'Sign Up' : 'Sign In'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
