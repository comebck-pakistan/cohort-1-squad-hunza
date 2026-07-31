import React, { useState } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Layout from '../../components/Layout';
import { useAppState } from '../../context/AppStateContext';
import {
  ArrowLeft,
  Paperclip,
  Send,
  Edit3,
  Trash2,
  RefreshCw,
  CheckCircle,
  FileText,
  Sparkles,
  AlertTriangle,
  ChevronDown,
} from 'lucide-react';

export default function EmailDetail() {
  const router = useRouter();
  const { email_id } = router.query;
  const {
    emails,
    categories,
    approveDraft,
    discardDraft,
    updateDraftText,
    updateEmailCategory,
    regenerateDraftText,
    generateDraft,
    setResumeModalUrl,
    setActiveResumeName,
  } = useAppState();

  const email = emails.find((e) => e.id === email_id);

  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [draftText, setDraftText] = useState<string>('');
  const [isGenerating, setIsGenerating] = useState<boolean>(false);

  // Sync draft text when email changes
  React.useEffect(() => {
    if (email && email.draftReply) {
      setDraftText(email.draftReply.text);
    }
  }, [email]);

  const handleGenerateDraft = async () => {
    if (!email) return;
    setIsGenerating(true);
    await generateDraft(email.id);
    setIsGenerating(false);
  };

  if (!email) {
    return (
      <Layout>
        <div className="text-center py-20 space-y-4">
          <p className="text-sm font-bold text-zinc-500">Email document not found.</p>
          <Link
            href="/inbox"
            className="inline-flex items-center gap-2 bg-zinc-900 text-white font-bold px-4 py-2 rounded-xl text-xs"
          >
            <ArrowLeft className="w-4 h-4" /> Return to Inbox
          </Link>
        </div>
      </Layout>
    );
  }

  const handleSaveEdits = () => {
    updateDraftText(email.id, draftText);
    setIsEditing(false);
  };

  const handleOpenResume = () => {
    setResumeModalUrl(
      'https://wanvhvtdpynebwlvorpw.supabase.co/storage/v1/object/public/resumes/john_smith_resume.pdf'
    );
    setActiveResumeName(email.attachmentName || 'Candidate Resume');
  };

  return (
    <Layout>
      {/* Top Header Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link
            href="/inbox"
            className="w-9 h-9 rounded-2xl bg-[#FBF9F5] border border-[#EAE3D5] flex items-center justify-center text-zinc-600 hover:text-zinc-900 hover:bg-[#EFE9DE] transition-all"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-xl font-extrabold text-zinc-900 tracking-tight">{email.subject}</h1>
            <p className="text-xs text-zinc-500 font-medium">Thread ID: {email.id}</p>
          </div>
        </div>

        {/* Category correction dropdown */}
        <div className="flex items-center gap-2 bg-[#FBF9F5] border border-[#EAE3D5] p-1.5 rounded-2xl">
          <span className="text-xs font-bold text-zinc-400 pl-2">Category:</span>
          <select
            value={email.category}
            onChange={(e) => updateEmailCategory(email.id, e.target.value)}
            className="bg-[#EFE9DE] text-zinc-900 font-extrabold text-xs px-3 py-1.5 rounded-xl border-none focus:outline-none cursor-pointer"
          >
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Two Panel Layout Side by Side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Panel — Original Email */}
        <div className="nixtio-card p-6 space-y-6 flex flex-col justify-between">
          <div className="space-y-4">
            {/* Sender Header */}
            <div className="flex items-start justify-between border-b border-[#EAE3D5] pb-4">
              <div className="flex items-center gap-3">
                {email.avatarUrl ? (
                  <img
                    src={email.avatarUrl}
                    alt={email.senderName}
                    className="w-11 h-11 rounded-full object-cover border-2 border-amber-300 shadow-sm"
                  />
                ) : (
                  <div className="w-11 h-11 rounded-full bg-amber-400/20 text-amber-900 font-extrabold text-base flex items-center justify-center border-2 border-amber-300">
                    {email.senderName.charAt(0)}
                  </div>
                )}
                <div>
                  <h3 className="font-extrabold text-zinc-900 text-sm">{email.senderName}</h3>
                  <p className="text-xs text-zinc-500 font-mono">{email.senderEmail}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-[11px] font-mono text-zinc-400">{email.date}</p>
                <span className="text-[10px] font-bold text-amber-900 bg-amber-100 px-2 py-0.5 rounded-full mt-1 inline-block">
                  Priority: {email.priority}
                </span>
              </div>
            </div>

            {/* Email Body */}
            <div className="space-y-3 pt-2">
              <p className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Original Email Message</p>
              <div className="p-4 bg-[#EFE9DE]/50 border border-[#E8E1D2] rounded-2xl text-xs text-zinc-800 font-medium leading-relaxed whitespace-pre-line min-h-[160px]">
                {email.body}
              </div>
            </div>

            {/* Attachment preview if exists */}
            {email.attachmentName && (
              <div className="p-4 bg-[#FBF9F5] border border-[#EAE3D5] rounded-2xl flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-amber-400/20 text-amber-800 flex items-center justify-center font-bold">
                    <Paperclip className="w-4 h-4 text-amber-700" />
                  </div>
                  <div>
                    <p className="text-xs font-extrabold text-zinc-900">{email.attachmentName}</p>
                    <p className="text-[10px] text-zinc-400 font-mono">{email.attachmentSize || '1.4 MB'}</p>
                  </div>
                </div>
                <button
                  onClick={handleOpenResume}
                  className="bg-zinc-900 hover:bg-zinc-800 text-white text-xs font-bold px-3.5 py-1.5 rounded-xl transition-all shadow-xs"
                >
                  View Attachment
                </button>
              </div>
            )}
          </div>

          <div className="pt-4 border-t border-[#EAE3D5] text-[11px] text-zinc-400 font-semibold flex items-center justify-between">
            <span>Status: {email.status}</span>
            <span>Language: English (US)</span>
          </div>
        </div>

        {/* Right Panel — AI Draft Reply */}
        <div className="nixtio-card p-6 space-y-6 flex flex-col justify-between">
          {email.draftReply ? (
            <>
              <div className="space-y-4">
                {/* AI Warning Banner */}
                <div className="bg-amber-400/15 border border-amber-300 p-4 rounded-2xl flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <Sparkles className="w-5 h-5 text-amber-600 shrink-0 animate-pulse" />
                    <div>
                      <h4 className="text-xs font-extrabold text-amber-950">AI Generated Response</h4>
                      <p className="text-[11px] text-amber-800 font-medium">
                        ⚠️ Not sent yet — awaiting your explicit review & approval
                      </p>
                    </div>
                  </div>
                  <span className="text-[10px] font-bold bg-amber-300 text-amber-950 px-2 py-0.5 rounded-full">
                    Tone: {email.draftReply?.tone || 'Friendly'}
                  </span>
                </div>

                {/* Draft Content / Editor */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-bold text-zinc-400 uppercase tracking-wider">
                      {isEditing ? 'Editing Draft Text' : 'Proposed Draft Reply'}
                    </label>
                    {!isEditing && (
                      <button
                        onClick={() => regenerateDraftText(email.id)}
                        className="text-xs font-bold text-zinc-600 hover:text-zinc-900 flex items-center gap-1 cursor-pointer"
                      >
                        <RefreshCw className="w-3 h-3 text-amber-500" /> Regenerate Tone
                      </button>
                    )}
                  </div>

                  {isEditing ? (
                    <textarea
                      rows={8}
                      value={draftText}
                      onChange={(e) => setDraftText(e.target.value)}
                      className="w-full bg-white border-2 border-amber-400 rounded-2xl p-4 text-xs font-medium text-zinc-900 leading-relaxed focus:outline-none shadow-sm"
                    ></textarea>
                  ) : (
                    <div className="p-4 bg-white border border-[#EAE3D5] rounded-2xl text-xs text-zinc-800 font-medium leading-relaxed whitespace-pre-line min-h-[200px] shadow-xs">
                      {email.draftReply.text}
                    </div>
                  )}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-4 border-t border-[#EAE3D5] flex flex-wrap items-center justify-between gap-3">
                <button
                  onClick={() => discardDraft(email.id)}
                  className="px-4 py-2.5 rounded-xl border border-rose-300 text-rose-700 hover:bg-rose-50 text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer"
                >
                  <Trash2 className="w-4 h-4" /> Discard
                </button>

                <div className="flex items-center gap-2">
                  {isEditing ? (
                    <button
                      onClick={handleSaveEdits}
                      className="bg-amber-400 hover:bg-amber-500 text-zinc-900 text-xs font-bold px-4 py-2.5 rounded-xl shadow-xs transition-all cursor-pointer"
                    >
                      Save Edits
                    </button>
                  ) : (
                    <button
                      onClick={() => setIsEditing(true)}
                      className="bg-[#EFE9DE] hover:bg-[#E4DCCF] text-zinc-800 text-xs font-bold px-4 py-2.5 rounded-xl transition-all flex items-center gap-1.5 cursor-pointer"
                    >
                      <Edit3 className="w-4 h-4" /> Edit Text
                    </button>
                  )}

                  <button
                    onClick={() => approveDraft(email.id)}
                    disabled={email.draftReply.status === 'approved'}
                    className="bg-emerald-600 hover:bg-emerald-700 disabled:opacity-60 text-white text-xs font-bold px-5 py-2.5 rounded-xl shadow-md transition-all flex items-center gap-2 cursor-pointer"
                  >
                    <Send className="w-4 h-4" />
                    <span>{email.draftReply.status === 'approved' ? 'Sent' : 'Approve & Send'}</span>
                  </button>
                </div>
              </div>
            </>
          ) : (
            /* When no draft exists yet */
            <div className="flex-1 flex flex-col items-center justify-center py-16 px-6 text-center space-y-5 bg-[#FBF9F5] border border-dashed border-[#D6CDBA] rounded-2xl">
              <div className="w-12 h-12 rounded-2xl bg-amber-100 border border-amber-200 text-amber-700 flex items-center justify-center">
                <Sparkles className="w-6 h-6 animate-pulse text-amber-600" />
              </div>
              <div className="space-y-1">
                <h3 className="text-base font-extrabold text-zinc-900">No draft yet</h3>
                <p className="text-xs text-zinc-500 max-w-xs">
                  Generate an AI-powered draft reply tailored to this candidate message and job requirements.
                </p>
              </div>

              <button
                onClick={handleGenerateDraft}
                disabled={isGenerating}
                className="bg-zinc-900 hover:bg-zinc-800 disabled:opacity-50 text-white text-xs font-bold px-6 py-3 rounded-xl shadow-md transition-all flex items-center gap-2 cursor-pointer group"
              >
                <Sparkles className="w-4 h-4 text-amber-400 group-hover:rotate-12 transition-transform" />
                <span>{isGenerating ? 'Generating Draft...' : '✨ Generate Draft'}</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}
