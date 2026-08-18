import React, { useState, useEffect } from 'react';import Layout from '../components/Layout';
import { useAppState } from '../context/AppStateContext';
import {
  Settings,
  Layers,
  Briefcase,
  Mail,
  MessageSquare,
  Plus,
  Trash2,
  Check,
  ShieldCheck,
  LogOut,
} from 'lucide-react';

export default function SettingsPage() {
  const {
    categories,
    addCategory,
    removeCategory,
    jobRoles,
    addJobRole,
    removeJobRole,
    isGmailConnected,
    setGmailConnected,
    gmailAddress,
    replyTone,
    updateReplyTone,
    showToast,
} = useAppState();

const [newCatInput, setNewCatInput] = useState<string>('');
const [newRoleInput, setNewRoleInput] = useState<string>('');
const [selectedTone, setSelectedTone] = useState<'Formal' | 'Friendly' | 'Brief'>(
  (replyTone as 'Formal' | 'Friendly' | 'Brief') || 'Friendly'
);

useEffect(() => {
  setSelectedTone((replyTone as 'Formal' | 'Friendly' | 'Brief') || 'Friendly');
}, [replyTone]);

  const handleAddCat = () => {
    if (!newCatInput.trim()) return;
    addCategory(newCatInput.trim());
    setNewCatInput('');
  };

  const handleAddRole = () => {
    if (!newRoleInput.trim()) return;
    addJobRole(newRoleInput.trim());
    setNewRoleInput('');
  };

  const handleSavePreferences = () => {
    updateReplyTone(selectedTone);
    showToast('⚙️ Settings & Reply preferences saved successfully!');
};

return (
    <Layout>
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-extrabold text-zinc-900 tracking-tight">System Settings</h1>
        <p className="text-xs text-zinc-500 font-semibold mt-1">
          Manage AI classification rules, active job requisitions, and Gmail OAuth connections
        </p>
      </div>

      <div className="space-y-8 max-w-4xl">
        {/* Section 1 — Email Categories */}
        <div className="nixtio-card p-6 space-y-4">
          <div className="flex items-center gap-2 border-b border-[#EAE3D5] pb-3">
            <Layers className="w-5 h-5 text-amber-500" />
            <h2 className="text-base font-extrabold text-zinc-900">Section 1 — Email Categories</h2>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="text"
              value={newCatInput}
              onChange={(e) => setNewCatInput(e.target.value)}
              placeholder="Add new category..."
              className="flex-1 bg-[#FBF9F5] border border-[#EAE3D5] rounded-xl px-4 py-2 text-xs font-medium text-zinc-900 focus:outline-none focus:ring-2 focus:ring-amber-400"
            />
            <button
              onClick={handleAddCat}
              className="bg-zinc-900 hover:bg-zinc-800 text-white text-xs font-bold px-4 py-2 rounded-xl flex items-center gap-1 transition-all"
            >
              <Plus className="w-4 h-4 text-amber-400" /> Add Category
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5 pt-2">
            {categories.map((cat) => (
              <div
                key={cat}
                className="p-3 bg-[#EFE9DE]/60 border border-[#E8E1D2] rounded-xl flex items-center justify-between text-xs font-bold text-zinc-800"
              >
                <span>{cat}</span>
                <button
                  onClick={() => removeCategory(cat)}
                  className="text-zinc-400 hover:text-rose-600 transition-colors p-1"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Section 2 — Open Job Roles */}
        <div className="nixtio-card p-6 space-y-4">
          <div className="flex items-center gap-2 border-b border-[#EAE3D5] pb-3">
            <Briefcase className="w-5 h-5 text-amber-500" />
            <h2 className="text-base font-extrabold text-zinc-900">Section 2 — Open Job Roles</h2>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="text"
              value={newRoleInput}
              onChange={(e) => setNewRoleInput(e.target.value)}
              placeholder="e.g. Senior Frontend Engineer..."
              className="flex-1 bg-[#FBF9F5] border border-[#EAE3D5] rounded-xl px-4 py-2 text-xs font-medium text-zinc-900 focus:outline-none focus:ring-2 focus:ring-amber-400"
            />
            <button
              onClick={handleAddRole}
              className="bg-zinc-900 hover:bg-zinc-800 text-white text-xs font-bold px-4 py-2 rounded-xl flex items-center gap-1 transition-all"
            >
              <Plus className="w-4 h-4 text-amber-400" /> Add Role
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
            {jobRoles.map((role) => (
              <div
                key={role}
                className="p-3.5 bg-[#EFE9DE]/60 border border-[#E8E1D2] rounded-xl flex items-center justify-between text-xs font-bold text-zinc-900"
              >
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-amber-400"></span>
                  <span>{role}</span>
                </div>
                <button
                  onClick={() => removeJobRole(role)}
                  className="text-zinc-400 hover:text-rose-600 transition-colors p-1"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Section 3 — Gmail Connection */}
        <div className="nixtio-card p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-[#EAE3D5] pb-3">
            <div className="flex items-center gap-2">
              <Mail className="w-5 h-5 text-amber-500" />
              <h2 className="text-base font-extrabold text-zinc-900">Section 3 — Gmail Connection</h2>
            </div>

            {isGmailConnected ? (
              <span className="bg-emerald-100 text-emerald-800 border border-emerald-300 font-extrabold text-xs px-3 py-1 rounded-full flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" /> Connected
              </span>
            ) : (
              <span className="bg-rose-100 text-rose-800 border border-rose-300 font-extrabold text-xs px-3 py-1 rounded-full">
                Disconnected
              </span>
            )}
          </div>

          <div className="p-4 bg-[#EFE9DE]/60 border border-[#E8E1D2] rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <p className="text-xs font-extrabold text-zinc-900">Connected Account:</p>
              <p className="text-xs text-zinc-600 font-mono font-semibold">{gmailAddress || 'Not connected'}</p>
            </div>

            {isGmailConnected ? (
              <button
                onClick={() => setGmailConnected(false)}
                className="bg-rose-100 hover:bg-rose-200 text-rose-800 text-xs font-bold px-4 py-2 rounded-xl transition-all flex items-center gap-1.5"
              >
                <LogOut className="w-3.5 h-3.5 text-rose-600" /> Disconnect Gmail
              </button>
            ) : (
              <button
                onClick={() => setGmailConnected(true)}
                className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-4 py-2 rounded-xl transition-all"
              >
                Reconnect Gmail
              </button>
            )}
          </div>
        </div>

        {/* Section 4 — Reply Preferences */}
        <div className="nixtio-card p-6 space-y-6">
          <div className="flex items-center gap-2 border-b border-[#EAE3D5] pb-3">
            <MessageSquare className="w-5 h-5 text-amber-500" />
            <h2 className="text-base font-extrabold text-zinc-900">Section 4 — Reply Preferences</h2>
          </div>

          <div className="space-y-3">
            <label className="text-xs font-bold text-zinc-700">Default AI Tone Style</label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {[
                { tone: 'Formal', desc: 'Structured & professional' },
                { tone: 'Friendly', desc: 'Warm & conversational' },
                { tone: 'Brief', desc: 'Short & direct' },
              ].map((item) => (
                <button
                  key={item.tone}
                  onClick={() => setSelectedTone(item.tone as any)}
                  className={`p-4 rounded-2xl border text-left space-y-1 transition-all ${
                    selectedTone === item.tone
                      ? 'bg-zinc-900 text-white border-zinc-900 shadow-md'
                      : 'bg-[#EFE9DE]/60 border-[#E8E1D2] text-zinc-800 hover:border-zinc-400'
                  }`}
                >
                  <div className="flex items-center justify-between font-extrabold text-xs">
                    <span>{item.tone}</span>
                    {selectedTone === item.tone && <Check className="w-4 h-4 text-amber-400" />}
                  </div>
                  <p className={`text-[11px] ${selectedTone === item.tone ? 'text-zinc-300' : 'text-zinc-500'}`}>
                    {item.desc}
                  </p>
                </button>
              ))}
            </div>
          </div>

          <div className="pt-2 flex justify-end">
            <button
              onClick={handleSavePreferences}
              className="bg-zinc-900 hover:bg-zinc-800 text-white font-extrabold px-6 py-3 rounded-2xl text-xs shadow-md transition-all flex items-center gap-2"
            >
              <Check className="w-4 h-4 text-amber-400" /> Save Preferences
            </button>
          </div>
        </div>
      </div>
    </Layout>
  );
}
