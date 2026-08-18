import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { useAppState } from '../context/AppStateContext';
import confetti from 'canvas-confetti';
import { useAuth } from '../hooks/useAuth';
import { useRouter } from 'next/router';

import {
  CheckCircle2,
  Edit3,
  SkipForward,
  XCircle,
  Sparkles,
  Mail,
  Send,
  RefreshCw,
  FileCheck,
  Check,
} from 'lucide-react';

export default function DraftQueue() {
  const { emails, approveDraft, discardDraft, updateDraftText, showToast } = useAppState();

  const pendingEmails = emails.filter(
    (e) => e.draftReply && e.draftReply.status === 'pending'
  );
  const { session, loading } = useAuth();
const router = useRouter(); // skip if already imported/declared

useEffect(() => {
  if (!loading && !session) router.replace('/');
}, [loading, session, router]);

if (loading) return <div>Loading...</div>;
if (!session) return null;
  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [editedText, setEditedText] = useState<string>('');

  const currentEmail = pendingEmails[currentIndex];

  useEffect(() => {
    if (currentEmail && currentEmail.draftReply) {
      setEditedText(currentEmail.draftReply.text);
      setIsEditing(false);
    }
  }, [currentEmail, currentIndex]);

  useEffect(() => {
    if (pendingEmails.length === 0) {
      confetti({
        particleCount: 80,
        spread: 70,
        origin: { y: 0.6 },
      });
    }
  }, [pendingEmails.length]);

  const handleApproveCurrent = () => {
    if (!currentEmail) return;
    approveDraft(currentEmail.id);
    if (currentIndex >= pendingEmails.length - 1) {
      setCurrentIndex(0);
    }
  };

  const handleSkipCurrent = () => {
    showToast('Skipped draft review.');
    if (currentIndex < pendingEmails.length - 1) {
      setCurrentIndex((prev) => prev + 1);
    } else {
      setCurrentIndex(0);
    }
  };

  const handleRejectCurrent = () => {
    if (!currentEmail) return;
    discardDraft(currentEmail.id);
    if (currentIndex >= pendingEmails.length - 1) {
      setCurrentIndex(0);
    }
  };

  const handleSaveEdits = () => {
    if (!currentEmail) return;
    updateDraftText(currentEmail.id, editedText);
    setIsEditing(false);
  };

  return (
    <Layout>
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-zinc-900 tracking-tight">Draft Approval Queue</h1>
          <p className="text-xs text-zinc-500 font-semibold mt-1">
            Review and send AI generated responses one by one
          </p>
        </div>

        {pendingEmails.length > 0 && (
          <div className="flex items-center gap-3 flex-wrap">
            <div className="bg-amber-400 text-zinc-950 font-extrabold text-xs px-4 py-2 rounded-2xl shadow-sm flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-zinc-950" />
              <span>
                Draft {currentIndex + 1} of {pendingEmails.length} pending
              </span>
            </div>

            <select
              value={currentIndex}
              onChange={(e) => setCurrentIndex(Number(e.target.value))}
              className="bg-[#FBF9F5] border border-[#EAE3D5] rounded-2xl px-4 py-2.5 text-xs font-bold text-zinc-800 focus:outline-none focus:ring-2 focus:ring-amber-400 shadow-xs cursor-pointer max-w-[240px]"
            >
              {pendingEmails.map((email, index) => (
                <option key={email.id} value={index}>
                  {index + 1}. {email.senderName} — {email.subject}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Empty State */}
      {pendingEmails.length === 0 ? (
        <div className="nixtio-card p-12 text-center space-y-6 max-w-xl mx-auto my-12 animate-fadeIn">
          <div className="w-20 h-20 rounded-3xl bg-emerald-500 text-white flex items-center justify-center mx-auto shadow-nixtio-lg">
            <CheckCircle2 className="w-10 h-10" />
          </div>
          <div className="space-y-2">
            <h2 className="text-2xl font-extrabold text-zinc-900">All Drafts Reviewed!</h2>
            <p className="text-xs text-zinc-500 font-medium max-w-md mx-auto leading-relaxed">
              Your recruiting inbox queue is completely clear. Great job keeping up with applicant communications!
            </p>
          </div>
          <div className="pt-2">
            <a
              href="/inbox"
              className="inline-flex items-center gap-2 bg-zinc-900 text-white font-bold px-6 py-3 rounded-2xl text-xs shadow-md hover:bg-zinc-800 transition-all"
            >
              Return to Inbox
            </a>
          </div>
        </div>
      ) : (
        /* Active Draft Item Review Card */
        <div className="space-y-6">
          {/* Top Half — Original Email (Read Only) */}
          <div className="nixtio-card p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-[#EAE3D5] pb-3">
              <div className="flex items-center gap-3">
                {currentEmail.avatarUrl ? (
                  <img
                    src={currentEmail.avatarUrl}
                    alt={currentEmail.senderName}
                    className="w-10 h-10 rounded-full object-cover border-2 border-amber-300"
                  />
                ) : (
                  <div className="w-10 h-10 rounded-full bg-amber-400/20 text-amber-900 font-bold text-xs flex items-center justify-center">
                    {currentEmail.senderName.charAt(0)}
                  </div>
                )}
                <div>
                  <h3 className="font-extrabold text-zinc-900 text-sm">{currentEmail.senderName}</h3>
                  <p className="text-xs text-zinc-500 font-mono">{currentEmail.senderEmail}</p>
                </div>
              </div>
              <span className="text-xs font-bold text-zinc-600 bg-[#EFE9DE] px-3 py-1 rounded-full">
                {currentEmail.category}
              </span>
            </div>

            <div className="space-y-2">
              <p className="text-xs font-bold text-zinc-400 uppercase tracking-wider">
                Subject: {currentEmail.subject}
              </p>
              <div className="p-4 bg-[#EFE9DE]/50 border border-[#E8E1D2] rounded-2xl text-xs text-zinc-800 font-medium leading-relaxed max-h-40 overflow-y-auto">
                {currentEmail.body}
              </div>
            </div>
          </div>

          {/* Bottom Half — AI Draft (Editable) */}
          <div className="nixtio-card p-6 space-y-4 bg-white">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-amber-500" />
                <h3 className="text-sm font-extrabold text-zinc-900">
                  {isEditing ? 'Editing AI Draft Response' : 'Generated AI Response'}
                </h3>
              </div>
              <span className="text-[10px] font-bold bg-amber-100 text-amber-900 px-2.5 py-0.5 rounded-full">
                Tone: {currentEmail.draftReply?.tone || 'Friendly'}
              </span>
            </div>

            {isEditing ? (
              <textarea
                rows={6}
                value={editedText}
                onChange={(e) => setEditedText(e.target.value)}
                className="w-full bg-[#FBF9F5] border-2 border-amber-400 rounded-2xl p-4 text-xs font-medium text-zinc-900 leading-relaxed focus:outline-none"
              ></textarea>
            ) : (
              <div className="p-4 bg-[#FBF9F5] border border-[#EAE3D5] rounded-2xl text-xs text-zinc-800 font-medium leading-relaxed whitespace-pre-line">
                {currentEmail.draftReply?.text}
              </div>
            )}
          </div>

          {/* Four Big Buttons Row */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <button
              onClick={handleApproveCurrent}
              className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-extrabold py-4 px-4 rounded-2xl shadow-md transition-all flex items-center justify-center gap-2 text-xs"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>Approve & Send</span>
            </button>

            {isEditing ? (
              <button
                onClick={handleSaveEdits}
                className="w-full bg-amber-400 hover:bg-amber-500 text-zinc-950 font-extrabold py-4 px-4 rounded-2xl shadow-sm transition-all flex items-center justify-center gap-2 text-xs"
              >
                <Check className="w-4 h-4" />
                <span>Save Edits</span>
              </button>
            ) : (
              <button
                onClick={() => setIsEditing(true)}
                className="w-full bg-zinc-900 hover:bg-zinc-800 text-white font-extrabold py-4 px-4 rounded-2xl shadow-sm transition-all flex items-center justify-center gap-2 text-xs"
              >
                <Edit3 className="w-4 h-4 text-amber-400" />
                <span>Edit</span>
              </button>
            )}

            <button
              onClick={handleSkipCurrent}
              className="w-full bg-[#EFE9DE] hover:bg-[#E4DCCF] text-zinc-800 font-extrabold py-4 px-4 rounded-2xl transition-all flex items-center justify-center gap-2 text-xs"
            >
              <SkipForward className="w-4 h-4 text-zinc-600" />
              <span>Skip</span>
            </button>

            <button
              onClick={handleRejectCurrent}
              className="w-full bg-rose-100 hover:bg-rose-200 text-rose-800 font-extrabold py-4 px-4 rounded-2xl transition-all flex items-center justify-center gap-2 text-xs"
            >
              <XCircle className="w-4 h-4 text-rose-600" />
              <span>Reject</span>
            </button>
          </div>
        </div>
      )}
    </Layout>
  );
}
