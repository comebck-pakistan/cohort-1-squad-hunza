import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { supabase } from '../lib/supabase';
import { apiService } from '../lib/api';
import { Shield, ArrowRight } from 'lucide-react';

export default function Landing() {
  const router = useRouter();
  const [checking, setChecking] = useState(true);
  const [loadingAction, setLoadingAction] = useState<'signup' | 'login' | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    const checkExisting = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      if (session) {
        try {
          const status = await apiService.getGmailStatus();
          const hasActive = Array.isArray(status) && status.some((c: any) => c.is_active);
          if (hasActive) {
            router.replace('/dashboard');
            return;
          }
        } catch {
          // fall through to landing
        }
      }
      setChecking(false);
    };
    checkExisting();
  }, [router]);

  const handleAuth = async (intent: 'signup' | 'login') => {
    setLoadingAction(intent);
    setErrorMsg(null);
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${window.location.origin}/auth-callback?intent=${intent}`,
        },
      });
      if (error) throw error;
    } catch (err) {
      console.error('Auth failed', err);
      setErrorMsg('Authentication failed. Please try again.');
      setLoadingAction(null);
    }
  };

  if (checking) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#EFE9DE]">
        <p className="text-xs font-bold text-zinc-500">Loading...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-[#EFE9DE] bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-amber-100/60 via-[#EFE9DE] to-[#E5DEC9]">
      <div className="w-full max-w-md bg-[#FBF9F5] border border-[#EAE3D5] rounded-3xl p-8 shadow-nixtio-lg space-y-6 relative overflow-hidden">
        <div className="absolute -top-12 -right-12 w-32 h-32 bg-amber-300/30 rounded-full blur-2xl pointer-events-none"></div>

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

        {errorMsg && (
          <div className="bg-rose-50 border border-rose-200 text-rose-800 text-xs font-bold px-4 py-3 rounded-xl text-center">
            {errorMsg}
          </div>
        )}

        <div className="space-y-3 pt-2">
          <button
            onClick={() => handleAuth('signup')}
            disabled={loadingAction !== null}
            className="w-full bg-zinc-900 hover:bg-zinc-800 text-white font-bold py-3.5 px-4 rounded-2xl shadow-md transition-all duration-200 flex items-center justify-center gap-3 group disabled:opacity-60"
          >
            <span>{loadingAction === 'signup' ? 'Redirecting...' : 'Sign Up'}</span>
            <ArrowRight className="w-4 h-4 text-amber-400 group-hover:translate-x-1 transition-transform" />
          </button>

          <button
            onClick={() => handleAuth('login')}
            disabled={loadingAction !== null}
            className="w-full bg-[#EFE9DE] hover:bg-[#E4DCCF] text-zinc-800 font-bold py-3.5 px-4 rounded-2xl transition-all duration-200 flex items-center justify-center gap-3 disabled:opacity-60"
          >
            <span>{loadingAction === 'login' ? 'Redirecting...' : 'Log In'}</span>
          </button>
        </div>

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