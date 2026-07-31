import React from 'react';
import { useAppState } from '../context/AppStateContext';
import { Sparkles } from 'lucide-react';

export default function Toast() {
  const { toastMessage } = useAppState();

  if (!toastMessage) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 animate-bounce">
      <div className="bg-zinc-900 text-white border border-zinc-700 px-5 py-3 rounded-2xl shadow-nixtio-lg flex items-center gap-3 text-xs font-bold">
        <Sparkles className="w-4 h-4 text-amber-400" />
        <span>{toastMessage}</span>
      </div>
    </div>
  );
}
