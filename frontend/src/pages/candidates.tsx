import React, { useState , useEffect } from 'react';
import Link from 'next/link';
import Layout from '../components/Layout';
import { useAppState } from '../context/AppStateContext';
import { Search, Filter, FileText, Mail, Sparkles, User, Briefcase, Calendar } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useRouter } from 'next/router';

export default function Candidates() {
  const { candidates, jobRoles, setActiveResumeCandidate } = useAppState();
const { session, loading } = useAuth();
const router = useRouter(); // skip if already imported/declared

useEffect(() => {
  if (!loading && !session) router.replace('/');
}, [loading, session, router]);

if (loading) return <div>Loading...</div>;
if (!session) return null;
  const [selectedRole, setSelectedRole] = useState<string>('All');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const filteredCandidates = candidates.filter((c) => {
    const matchesRole = selectedRole === 'All' || c.role === selectedRole;
    const q = searchQuery.toLowerCase();
    const matchesSearch =
      !q ||
      c.name.toLowerCase().includes(q) ||
      c.skills.some((s) => s.toLowerCase().includes(q)) ||
      c.role.toLowerCase().includes(q) ||
      c.summary.toLowerCase().includes(q);
    return matchesRole && matchesSearch;
  });

  const handleOpenResume = (candidate: any) => {
    setActiveResumeCandidate(candidate);
  };

  return (
    <Layout>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-zinc-900 tracking-tight">Candidate Library</h1>
          <p className="text-xs text-zinc-500 font-semibold mt-1">
            Semantic search & resume documents repository for applicant profiles
          </p>
        </div>

        {/* Search Bar */}
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-zinc-400 absolute left-3.5 top-3" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder='Semantic search e.g. "Python ML experience"...'
            className="w-full bg-[#FBF9F5] border border-[#EAE3D5] rounded-2xl pl-10 pr-4 py-2.5 text-xs font-medium text-zinc-900 focus:outline-none focus:ring-2 focus:ring-amber-400 shadow-xs"
          />
        </div>
      </div>

      {/* Controls Row */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-[#FBF9F5] border border-[#EAE3D5] p-3 rounded-2xl">
        <div className="flex items-center gap-3">
          <Filter className="w-4 h-4 text-zinc-400" />
          <span className="text-xs font-bold text-zinc-600">Filter by Role:</span>
          <select
            value={selectedRole}
            onChange={(e) => setSelectedRole(e.target.value)}
            className="bg-[#EFE9DE] border border-[#E4DCCF] text-zinc-900 font-bold text-xs px-3.5 py-1.5 rounded-xl focus:outline-none cursor-pointer"
          >
            <option value="All">All Job Roles ({candidates.length})</option>
            {jobRoles.map((role) => (
              <option key={role} value={role}>
                {role}
              </option>
            ))}
          </select>
        </div>

        <div className="text-xs font-bold text-zinc-500 flex items-center gap-2">
          <Sparkles className="w-3.5 h-3.5 text-amber-500" />
          <span>Showing {filteredCandidates.length} candidate profiles</span>
        </div>
      </div>

      {/* Candidates Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {filteredCandidates.map((candidate) => (
          <div
            key={candidate.id}
            className="nixtio-card p-6 flex flex-col justify-between space-y-4 hover:border-zinc-400 transition-all group"
          >
            <div className="space-y-4">
              {/* Header Info */}
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <img
                    src={candidate.avatarUrl}
                    alt={candidate.name}
                    className="w-12 h-12 rounded-full object-cover border-2 border-amber-400 shadow-sm"
                  />
                  <div>
                    <h3 className="font-extrabold text-zinc-900 text-base group-hover:text-amber-800 transition-colors">
                      👤 {candidate.name}
                    </h3>
                    <p className="text-xs text-amber-900 bg-amber-100 border border-amber-200 px-2.5 py-0.5 rounded-full inline-block font-bold mt-0.5">
                      {candidate.role}
                    </p>
                  </div>
                </div>

                <span className="text-[11px] font-mono font-semibold text-zinc-400">
                  Applied: {candidate.appliedDate}
                </span>
              </div>

              {/* Summary */}
              <p className="text-xs text-zinc-600 font-medium leading-relaxed bg-[#EFE9DE]/50 border border-[#E8E1D2] p-3 rounded-xl line-clamp-2">
                {candidate.summary}
              </p>

              {/* Skills Tags */}
              <div className="space-y-1.5">
                <p className="text-[10px] font-bold uppercase tracking-wider text-zinc-400">Top Skills</p>
                <div className="flex flex-wrap gap-1.5">
                  {candidate.skills.map((skill) => (
                    <span
                      key={skill}
                      className="bg-[#EFE9DE] text-zinc-800 text-[11px] font-bold px-2.5 py-1 rounded-lg border border-[#E2DACB]"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Action buttons */}
            <div className="pt-4 border-t border-[#EAE3D5] flex items-center justify-between gap-3">
              <button
                onClick={() => handleOpenResume(candidate)}
                className="bg-zinc-900 hover:bg-zinc-800 text-white text-xs font-bold px-4 py-2 rounded-xl transition-all shadow-xs flex items-center gap-1.5"
              >
                <FileText className="w-3.5 h-3.5 text-amber-400" /> View Resume
              </button>

              {candidate.emailId && (
                <Link
                  href={`/inbox/${candidate.emailId}`}
                  className="bg-[#EFE9DE] hover:bg-[#E4DCCF] text-zinc-800 text-xs font-bold px-4 py-2 rounded-xl transition-all flex items-center gap-1.5"
                >
                  <Mail className="w-3.5 h-3.5 text-zinc-600" /> Original Email
                </Link>
              )}
            </div>
          </div>
        ))}
      </div>
    </Layout>
  );
}
