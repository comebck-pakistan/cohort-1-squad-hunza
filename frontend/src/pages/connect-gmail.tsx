import React, { useState } from 'react';
import { useRouter } from 'next/router';
import { Mail, CheckCircle2, ShieldCheck, ArrowRight, Lock } from 'lucide-react';
import { useAppState } from '../context/AppStateContext';

export default function ConnectGmail() {
  const router = useRouter();
  const { setGmailConnected } = useAppState();
  const [connecting, setConnecting] = useState(false);
  const [connected, setConnected] = useState(false);

  const handleConnectGmail = async () => {
    setConnecting(true);
    // Simulate API call to GET /auth/gmail/connect
    setTimeout(() => {
      setConnecting(false);
      setConnected(true);
      setGmailConnected(true);
    }, 800);
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-[#EFE9DE]">
      <div className="w-full max-w-lg bg-[#FBF9F5] border border-[#EAE3D5] rounded-3xl p-8 shadow-nixtio-lg space-y-6">
        {/* Header */}
        <div className="text-center space-y-3">
          <div className="w-16 h-16 rounded-2xl bg-amber-400/20 text-amber-900 flex items-center justify-center mx-auto border border-amber-300">
            <Mail className="w-8 h-8 text-amber-800" />
          </div>
          <div>
            <h1 className="text-2xl font-extrabold text-zinc-900 tracking-tight">Connect Your Gmail Inbox</h1>
            <p className="text-xs text-zinc-500 font-medium mt-1">
              Grant permissions so our AI assistant can manage HR communications.
            </p>
          </div>
        </div>

        {/* Status indicator or Features list */}
        {connected ? (
          <div className="bg-emerald-50 border border-emerald-200 p-6 rounded-2xl text-center space-y-4 animate-fadeIn">
            <div className="w-12 h-12 rounded-full bg-emerald-500 text-white flex items-center justify-center mx-auto shadow-md">
              <CheckCircle2 className="w-7 h-7" />
            </div>
            <div>
              <h3 className="font-extrabold text-emerald-950 text-base">✅ Gmail Connected Successfully</h3>
              <p className="text-xs text-emerald-700 font-medium mt-1">
                Authorized for <span className="font-bold">sarah.jenkins@crextio.hr</span>
              </p>
            </div>
            <button
              onClick={() => router.push('/onboarding')}
              className="w-full bg-zinc-900 hover:bg-zinc-800 text-white font-bold py-3 px-4 rounded-xl shadow-md transition-all flex items-center justify-center gap-2"
            >
              <span>Continue to Setup</span>
              <ArrowRight className="w-4 h-4 text-amber-400" />
            </button>
          </div>
        ) : (
          <>
            {/* Required permissions cards */}
            <div className="bg-[#EFE9DE]/70 border border-[#E8E1D2] rounded-2xl p-5 space-y-3.5">
              <h3 className="text-xs font-extrabold text-zinc-400 uppercase tracking-wider">Requested Access</h3>
              <div className="space-y-2.5">
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <p className="text-xs font-semibold text-zinc-800 leading-relaxed">
                    Read incoming recruiter & applicant emails
                  </p>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <p className="text-xs font-semibold text-zinc-800 leading-relaxed">
                    Apply automatic HR labels & priority folders
                  </p>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <p className="text-xs font-semibold text-zinc-800 leading-relaxed">
                    Create draft replies on your behalf
                  </p>
                </div>
              </div>
            </div>

            {/* Action button */}
            <button
              onClick={handleConnectGmail}
              disabled={connecting}
              className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3.5 px-4 rounded-2xl shadow-md transition-all flex items-center justify-center gap-2"
            >
              <Mail className="w-4 h-4" />
              <span>{connecting ? 'Connecting OAuth...' : 'Connect Gmail Account'}</span>
            </button>
          </>
        )}

        {/* Small footer text */}
        <div className="pt-2 text-center">
          <p className="text-[11px] text-zinc-400 font-medium flex items-center justify-center gap-1">
            <Lock className="w-3 h-3 text-zinc-400" />
            We never send emails without your explicit approval
          </p>
        </div>
      </div>
    </div>
  );
}
