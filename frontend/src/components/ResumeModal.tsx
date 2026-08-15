import React from 'react';
import { X, FileText, Download, ExternalLink, CheckCircle } from 'lucide-react';
import { useAppState } from '../context/AppStateContext';

export default function ResumeModal() {
  const { activeResumeCandidate, setActiveResumeCandidate } = useAppState();

  if (!activeResumeCandidate) return null;

  const candidate = activeResumeCandidate;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-zinc-900/60 backdrop-blur-sm animate-fadeIn">
      <div className="bg-[#FBF9F5] border border-[#EAE3D5] rounded-3xl w-full max-w-3xl shadow-nixtio-lg overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-[#EAE3D5] flex items-center justify-between bg-[#EFE9DE]/80">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-amber-400/20 text-amber-800 flex items-center justify-center font-bold">
              <FileText className="w-5 h-5 text-amber-700" />
            </div>
            <div>
              <h3 className="font-extrabold text-base text-zinc-900">
                {candidate.name} - {candidate.resumeFileName || 'Resume'}
              </h3>
              <p className="text-xs text-zinc-500 font-medium flex items-center gap-1">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-600" /> Verified Supabase Storage Attachment
              </p>
            </div>
          </div>
          <button
            onClick={() => setActiveResumeCandidate(null)}
            className="w-8 h-8 rounded-full bg-zinc-200 text-zinc-700 hover:bg-zinc-900 hover:text-white flex items-center justify-center transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Document Body Preview */}
        <div className="p-6 overflow-y-auto flex-1 bg-white space-y-6">
          <div className="border border-zinc-200 rounded-2xl p-6 bg-zinc-50/50 space-y-4">
            <div className="flex items-start justify-between border-b border-zinc-200 pb-4">
              <div>
                <h4 className="text-xl font-extrabold text-zinc-900">Curriculum Vitae & Experience</h4>
                <p className="text-xs text-zinc-500 font-medium">Candidate Profile Overview — {candidate.role}</p>
              </div>
            </div>

            <div className="space-y-3 text-sm text-zinc-700 leading-relaxed">
              <p className="font-semibold text-zinc-900">Executive Summary:</p>
              <p className="bg-amber-50/60 border border-amber-200 p-3.5 rounded-xl text-xs text-amber-950 font-medium">
                {candidate.summary || 'No summary was extracted for this candidate.'}
              </p>

             <div className="grid grid-cols-2 gap-4 pt-2">
              <div className="bg-white border border-zinc-200 p-3 rounded-xl">
                <p className="text-[10px] font-bold uppercase text-zinc-400">Role Applied For</p>
                <p className="text-xs font-bold text-zinc-900">{candidate.role || 'Not specified'}</p>
              </div>
              <div className="bg-white border border-zinc-200 p-3 rounded-xl">
                <p className="text-[10px] font-bold uppercase text-zinc-400">Total Experience</p>
                <p className="text-xs font-bold text-zinc-900">
                  {candidate.experienceYears ? `${candidate.experienceYears}+ Years` : 'Not specified'}
                </p>
              </div>
              <div className="bg-white border border-zinc-200 p-3 rounded-xl">
                <p className="text-[10px] font-bold uppercase text-zinc-400">Education</p>
                <p className="text-xs font-bold text-zinc-900">
                  {candidate.educationDegree || 'Not specified'}
                </p>
                <p className="text-[11px] text-zinc-500">
                  {candidate.educationInstitution || ''}
                  {candidate.educationGpa ? ` • GPA: ${candidate.educationGpa}` : ''}
                </p>
              </div>
            </div>
            
              {candidate.skills && candidate.skills.length > 0 && (
                <div className="pt-2">
                  <p className="text-[10px] font-bold uppercase text-zinc-400 mb-1.5">Skills</p>
                  <div className="flex flex-wrap gap-1.5">
                    {candidate.skills.map((skill) => (
                      <span
                        key={skill}
                        className="bg-white text-zinc-800 text-[11px] font-bold px-2.5 py-1 rounded-lg border border-zinc-200"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Document link info */}
            <div className="p-3 bg-zinc-100 rounded-xl text-xs text-zinc-500 flex items-center justify-between">
              <span className="truncate max-w-md font-mono text-[11px]">{candidate.resumeUrl}</span>
            </div>
          </div>
        </div>

        {/* Modal Footer Controls */}
        <div className="px-6 py-4 border-t border-[#EAE3D5] flex items-center justify-between bg-[#FBF9F5]">
          <a
            href={candidate.resumeUrl}
            target="_blank"
            rel="noreferrer"
            className="text-xs font-bold text-zinc-600 hover:text-zinc-900 flex items-center gap-1.5"
          >
            Open in new tab <ExternalLink className="w-3.5 h-3.5" />
          </a>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setActiveResumeCandidate(null)}
              className="px-4 py-2 rounded-xl text-xs font-bold text-zinc-600 hover:bg-zinc-200 transition-all"
            >
              Close
            </button>

            <a
              href={candidate.resumeUrl}
              download
              className="px-4 py-2 rounded-xl text-xs font-bold bg-zinc-900 text-white hover:bg-zinc-800 shadow-sm flex items-center gap-1.5 transition-all"
            >
              <Download className="w-3.5 h-3.5" /> Download File
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}