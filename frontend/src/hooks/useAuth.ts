import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { supabase } from '../lib/supabase';

export function useAuth() {
  const [session, setSession] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const router = useRouter();

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        setSession(session);
      } else {
        // Provide mock fallback session for demo mode
        const mockSession = {
          user: {
            id: 'demo-hr-user-777',
            email: 'sarah.jenkins@crextio.hr',
            user_metadata: {
              full_name: 'Nixtio Admin',
              avatar_url: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80',
            },
          },
          access_token: 'mock-supabase-access-token',
        };
        setSession(mockSession);
      }
      setLoading(false);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session) {
        setSession(session);
      }
    });

    return () => subscription.unsubscribe();
  }, [router]);

  return { session, loading };
}
