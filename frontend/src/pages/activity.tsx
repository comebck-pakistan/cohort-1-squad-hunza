import React, { useState , useEffect } from 'react';
import Layout from '../components/Layout';
import { useAppState } from '../context/AppStateContext';
import { History, Filter, FileEdit, Tag, Calendar, UserCheck } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useRouter } from 'next/router';

export default function ActivityLog() {
  const { corrections } = useAppState();

  const { session, loading } = useAuth();
  const router = useRouter(); // skip if already imported/declared

  const [activeTab, setActiveTab] = useState<'Draft Edit' | 'Category Fix'>('Draft Edit');
  const [dateFilter, setDateFilter] = useState<string>('All');

  useEffect(() => {
    if (!loading && !session) router.replace('/');
  }, [loading, session, router]);

  if (loading) return <div>Loading...</div>;
  if (!session) return null;

  const filteredCorrections = corrections.filter((c) => c.type === activeTab);
  
  return (
    <Layout>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-zinc-900 tracking-tight">Activity & Corrections Log</h1>
          <p className="text-xs text-zinc-500 font-semibold mt-1">
            Audit history of recruiter draft edits and category classification corrections
          </p>
        </div>

        <div className="flex items-center gap-2 bg-[#FBF9F5] border border-[#EAE3D5] p-1.5 rounded-2xl">
          <Calendar className="w-4 h-4 text-zinc-400 ml-2" />
          <select
            value={dateFilter}
            onChange={(e) => setDateFilter(e.target.value)}
            className="bg-[#EFE9DE] text-zinc-900 font-bold text-xs px-3 py-1.5 rounded-xl border-none focus:outline-none cursor-pointer"
          >
            <option value="All">All Dates</option>
            <option value="Today">Today (Jul 28)</option>
            <option value="7days">Last 7 Days</option>
          </select>
        </div>
      </div>

      {/* Two Tabs Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => setActiveTab('Draft Edit')}
          className={`px-5 py-2.5 rounded-2xl text-xs font-extrabold transition-all flex items-center gap-2 ${
            activeTab === 'Draft Edit'
              ? 'bg-zinc-900 text-white shadow-md'
              : 'bg-[#FBF9F5] text-zinc-600 border border-[#EAE3D5] hover:bg-[#EFE9DE]'
          }`}
        >
          <FileEdit className={`w-4 h-4 ${activeTab === 'Draft Edit' ? 'text-amber-400' : 'text-zinc-500'}`} />
          <span>Draft Corrections</span>
        </button>

        <button
          onClick={() => setActiveTab('Category Fix')}
          className={`px-5 py-2.5 rounded-2xl text-xs font-extrabold transition-all flex items-center gap-2 ${
            activeTab === 'Category Fix'
              ? 'bg-zinc-900 text-white shadow-md'
              : 'bg-[#FBF9F5] text-zinc-600 border border-[#EAE3D5] hover:bg-[#EFE9DE]'
          }`}
        >
          <Tag className={`w-4 h-4 ${activeTab === 'Category Fix' ? 'text-amber-400' : 'text-zinc-500'}`} />
          <span>Category Corrections</span>
        </button>
      </div>

      {/* Audit Log Table */}
      <div className="nixtio-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#EAE3D5] bg-[#EFE9DE]/50 text-[11px] font-extrabold text-zinc-400 uppercase tracking-wider">
                <th className="py-3.5 px-6">Date</th>
                <th className="py-3.5 px-6">Target Email Subject</th>
                <th className="py-3.5 px-6">Original (AI Generated)</th>
                <th className="py-3.5 px-6">Corrected / Edit Summary</th>
                <th className="py-3.5 px-6">Corrected By</th>
                <th className="py-3.5 px-6 text-right">Type</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#EAE3D5] text-xs font-medium text-zinc-800">
              {filteredCorrections.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-zinc-400 font-semibold">
                    No corrections recorded yet for this tab.
                  </td>
                </tr>
              ) : (
                filteredCorrections.map((log) => (
                  <tr key={log.id} className="hover:bg-[#EFE9DE]/50 transition-colors">
                    <td className="py-4 px-6 font-mono text-[11px] text-zinc-500 font-semibold">{log.date}</td>
                    <td className="py-4 px-6 max-w-xs font-extrabold text-zinc-900 truncate">
                      {log.emailSubject}
                    </td>
                    <td className="py-4 px-6 max-w-xs text-zinc-500 font-mono text-[11px] truncate">
                      {log.original}
                    </td>
                    <td className="py-4 px-6 max-w-xs font-semibold text-zinc-900">{log.corrected}</td>
                    <td className="py-4 px-6 text-zinc-600 font-bold flex items-center gap-1.5 pt-5">
                      <UserCheck className="w-3.5 h-3.5 text-emerald-600" />
                      {log.correctedBy}
                    </td>
                    <td className="py-4 px-6 text-right font-extrabold">
                      <span
                        className={`text-[10px] px-2.5 py-1 rounded-full ${
                          log.type === 'Draft Edit'
                            ? 'bg-amber-100 text-amber-900 border border-amber-300'
                            : 'bg-sky-100 text-sky-900 border border-sky-300'
                        }`}
                      >
                        {log.type}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </Layout>
  );
}
