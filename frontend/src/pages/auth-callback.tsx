import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { supabase } from '../lib/supabase';
import { apiService } from '../lib/api';

export default function AuthCallback() {
  const router = useRouter();
  const [message, setMessage] = useState('Verifying your account...');

  useEffect(() => {
    if (!router.isReady) return;

    const run = async () => {
      const intent = router.query.intent === 'login' ? 'login' : 'signup';

      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        router.replace('/');
        return;
      }

      let connections: any[] = [];
      try {
        const status = await apiService.getGmailStatus();
        connections = Array.isArray(status) ? status : [];
      } catch (err) {
        console.error('Failed to check Gmail status', err);
      }

      const hasAnyConnection = connections.length > 0;
      const hasActiveConnection = connections.some((c: any) => c.is_active);

      if (intent === 'login') {
        if (!hasAnyConnection) {
          setMessage('No account found. Please sign up first.');
          await supabase.auth.signOut();
          setTimeout(() => router.replace('/'), 2500);
          return;
        }
        if (hasActiveConnection) {
          router.replace('/dashboard');
        } else {
          router.replace('/connect-gmail');
        }
        return;
      }

      // intent === 'signup'
      if (hasActiveConnection) {
        router.replace('/dashboard');
      } else if (hasAnyConnection) {
        router.replace('/connect-gmail');
      } else {
        router.replace('/onboarding');
      }
    };

    run();
  }, [router.isReady, router.query.intent, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#EFE9DE]">
      <p className="text-xs font-bold text-zinc-600">{message}</p>
    </div>
  );
}