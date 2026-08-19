import React, { useState } from 'react';
import { useRouter } from 'next/router';
import { supabase } from '../lib/supabase';
import { Sparkles, Shield, ArrowRight, Mail } from 'lucide-react';

export default function Login() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const handleGoogleLogin = async () => {
    setLoading(true);
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${window.location.origin}/auth-callback?intent=login`,
        },
      });
      if (error) {
        // Fallback for local demo mode
        router.push('/connect-gmail');
      }
    } catch {
      router.push('/connect-gmail');
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-[#EFE9DE] bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-amber-100/60 via-[#EFE9DE] to-[#E5DEC9]">
      <div className="w-full max-w-md bg-[#FBF9F5] border border-[#EAE3D5] rounded-3xl p-8 shadow-nixtio-lg space-y-6 relative overflow-hidden">
        {/* Ambient Top Glow */}
        <div className="absolute -top-12 -right-12 w-32 h-32 bg-amber-300/30 rounded-full blur-2xl pointer-events-none"></div>

        {/* Brand Header */}
        <div className="text-center space-y-3">
          <div className="w-14 h-14 rounded-2xl bg-zinc-900 text-amber-400 flex items-center justify-center font-black text-2xl mx-auto shadow-md">
            S
          </div>
          <div>
            <h1 className="text-2xl font-extrabold text-zinc-900 tracking-tight">Sortdesk HR Email Assistant</h1>
            <p className="text-xs text-zinc-500 font-medium mt-1">
              AI-powered inbox management for recruiters
            </p>
          </div>
        </div>

        {/* Action Button */}
        <div className="space-y-3 pt-2">
          <button
            onClick={handleGoogleLogin}
            disabled={loading}
            className="w-full bg-zinc-900 hover:bg-zinc-800 text-white font-bold py-3.5 px-4 rounded-2xl shadow-md transition-all duration-200 flex items-center justify-center gap-3 group"
          >
            <svg className="w-5 h-5 fill-current text-white" viewBox="0 0 24 24">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
            </svg>
            <span>{loading ? 'Authenticating...' : 'Sign in with Google'}</span>
            <ArrowRight className="w-4 h-4 text-amber-400 group-hover:translate-x-1 transition-transform" />
          </button>

        </div>

        {/* Footer text */}
        <div className="pt-4 border-t border-[#EAE3D5] text-center space-y-2">
          <p className="text-[11px] text-zinc-400 font-medium flex items-center justify-center gap-1.5">
            <Shield className="w-3.5 h-3.5 text-emerald-600" />
            Secure OAuth login powered by Supabase & Google
          </p>
        </div>
      </div>
    </div>
  );
}
