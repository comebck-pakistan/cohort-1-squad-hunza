import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import Layout from '../../components/Layout';
import { useAppState, mapBackendEmails } from '../../context/AppStateContext';
import { apiService } from '../../lib/api';
import { Search, Filter, Mail, ArrowUpRight, CheckCircle, Clock, Trash2 } from 'lucide-react';

const PAGE_SIZE = 50;

export default function InboxList() {
  const { categories, totalEmailCount, showToast } = useAppState();
  const [pageEmails, setPageEmails] = useState<any[]>([]);
  const [page, setPage] = useState(0);
  const [loadingPage, setLoadingPage] = useState(true);
  const [selectedCategoryTab, setSelectedCategoryTab] = useState<string>('All');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const filterTabs = ['All', ...categories];

  const fetchPage = useCallback(async (pageNum: number) => {
    setLoadingPage(true);
    try {
      const data = await apiService.getEmails(PAGE_SIZE, pageNum * PAGE_SIZE);
      const mapped = mapBackendEmails(Array.isArray(data) ? data : []);
      setPageEmails(mapped);
    } catch (err) {
      console.error('Failed to load emails page', err);
      showToast('Unable to load emails.');
    } finally {
      setLoadingPage(false);
    }
  }, [showToast]);

  useEffect(() => {
    fetchPage(page);
  }, [page, fetchPage]);

  const handleDelete = async (emailId: string) => {
    if (!confirm('Delete this email? This cannot be undone.')) return;
    setDeletingId(emailId);
    try {
      await apiService.deleteEmail(emailId);
      setPageEmails((prev) => prev.filter((e) => e.id !== emailId));
      showToast('Email deleted.');
    } catch (err) {
      console.error('Failed to delete email', err);
      showToast('Failed to delete email.');
    } finally {
      setDeletingId(null);
    }
  };

  const filteredEmails = pageEmails.filter((email) => {
    const matchesCategory =
      selectedCategoryTab === 'All' || email.category === selectedCategoryTab;
    const query = searchQuery.toLowerCase();
    const matchesSearch =
      !query ||
      email.senderName?.toLowerCase().includes(query) ||
      email.senderEmail?.toLowerCase().includes(query) ||
      email.subject?.toLowerCase().includes(query) ||
      email.body?.toLowerCase().includes(query);
    return matchesCategory && matchesSearch;
  });

  const getCategoryBadgeClass = (category: string) => {
    switch (category) {
      case 'New Applicant':
        return 'bg-emerald-100 text-emerald-900 border-emerald-300';
      case 'Spam':
        return 'bg-rose-100 text-rose-900 border-rose-300';
      case 'Interview Scheduling':
      case 'Interview Reschedule':
        return 'bg-sky-100 text-sky-900 border-sky-300';
      case 'Offer Acceptance':
        return 'bg-amber-100 text-amber-900 border-amber-300';
      default:
        return 'bg-zinc-200 text-zinc-800 border-zinc-300';
    }
  };

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'High':
        return <span className="text-xs font-bold text-rose-700 bg-rose-50 border border-rose-200 px-2 py-0.5 rounded-full">🔴 High</span>;
      case 'Medium':
        return <span className="text-xs font-bold text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-full">🟡 Med</span>;
      default:
        return <span className="text-xs font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">🟢 Low</span>;
    }
  };

  const totalPages = Math.max(1, Math.ceil(totalEmailCount / PAGE_SIZE));

  return (
    <Layout>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-zinc-900 tracking-tight">Recruiter Inbox</h1>
          <p className="text-xs text-zinc-500 font-semibold mt-1">
            Real-time categorized recruiter emails & candidate applications — {totalEmailCount} total
          </p>
        </div>

        {/* Live Search Bar */}
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-zinc-400 absolute left-3.5 top-3" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search sender, subject, keyword..."
            className="w-full bg-[#FBF9F5] border border-[#EAE3D5] rounded-2xl pl-10 pr-4 py-2.5 text-xs font-medium text-zinc-900 focus:outline-none focus:ring-2 focus:ring-amber-400 shadow-xs"
          />
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
        {filterTabs.map((tab) => {
          const isActive = selectedCategoryTab === tab;
          return (
            <button
              key={tab}
              onClick={() => setSelectedCategoryTab(tab)}
              className={`px-4 py-2 rounded-2xl text-xs font-bold whitespace-nowrap transition-all ${
                isActive
                  ? 'bg-zinc-900 text-white shadow-md'
                  : 'bg-[#FBF9F5] text-zinc-600 border border-[#EAE3D5] hover:bg-[#EFE9DE]'
              }`}
            >
              {tab}
            </button>
          );
        })}
      </div>

      {/* Email Table Card */}
      <div className="nixtio-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#EAE3D5] bg-[#EFE9DE]/50 text-[11px] font-extrabold text-zinc-400 uppercase tracking-wider">
                <th className="py-3.5 px-6">Sender</th>
                <th className="py-3.5 px-6">Subject</th>
                <th className="py-3.5 px-6">Category</th>
                <th className="py-3.5 px-6">Priority</th>
                <th className="py-3.5 px-6">Status</th>
                <th className="py-3.5 px-6 text-right">Date</th>
                <th className="py-3.5 px-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#EAE3D5] text-xs font-medium text-zinc-800">
              {loadingPage ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-zinc-400 font-semibold">
                    Loading emails...
                  </td>
                </tr>
              ) : filteredEmails.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-zinc-400 font-semibold">
                    No emails match the selected category filter or search query.
                  </td>
                </tr>
              ) : (
                filteredEmails.map((email) => (
                  <tr
                    key={email.id}
                    className="hover:bg-[#EFE9DE]/70 cursor-pointer transition-colors group"
                  >
                    {/* Sender */}
                    <td className="py-4 px-6">
                      <Link href={`/inbox/${email.id}`} className="block">
                        <div className="flex items-center gap-3">
                          {email.avatarUrl ? (
                            <img
                              src={email.avatarUrl}
                              alt={email.senderName}
                              className="w-8 h-8 rounded-full object-cover border border-amber-300"
                            />
                          ) : (
                            <div className="w-8 h-8 rounded-full bg-amber-400/20 text-amber-900 font-bold text-xs flex items-center justify-center border border-amber-300">
                              {email.senderName?.charAt(0)}
                            </div>
                          )}
                          <div>
                            <p className="font-extrabold text-zinc-900 group-hover:text-amber-800 transition-colors">
                              {email.senderName}
                            </p>
                            <p className="text-[10px] text-zinc-400 font-mono">{email.senderEmail}</p>
                          </div>
                        </div>
                      </Link>
                    </td>

                    {/* Subject */}
                    <td className="py-4 px-6 max-w-xs">
                      <Link href={`/inbox/${email.id}`} className="block">
                        <p className="font-bold text-zinc-900 truncate group-hover:text-amber-800 transition-colors">
                          {email.subject}
                        </p>
                        <p className="text-[11px] text-zinc-500 truncate line-clamp-1">{email.body}</p>
                      </Link>
                    </td>

                    {/* Category */}
                    <td className="py-4 px-6">
                      <span className={`text-[11px] font-bold px-2.5 py-1 rounded-full border ${getCategoryBadgeClass(email.category)}`}>
                        {email.category}
                      </span>
                    </td>

                    {/* Priority */}
                    <td className="py-4 px-6">{getPriorityBadge(email.priority)}</td>

                    {/* Status */}
                    <td className="py-4 px-6">
                      <span className="inline-flex items-center gap-1 font-bold text-zinc-700 bg-zinc-100 px-2.5 py-1 rounded-full text-[11px]">
                        {email.status === 'Approved & Sent' && <CheckCircle className="w-3 h-3 text-emerald-600" />}
                        {email.status === 'Draft Ready' && <Clock className="w-3 h-3 text-amber-500" />}
                        {email.status}
                      </span>
                    </td>

                    {/* Date */}
                    <td className="py-4 px-6 text-right font-mono text-[11px] text-zinc-500">
                      {email.date}
                    </td>

                    {/* Actions */}
                    <td className="py-4 px-6 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(email.id);
                        }}
                        disabled={deletingId === email.id}
                        className="p-2 rounded-xl text-zinc-400 hover:text-rose-600 hover:bg-rose-50 transition-colors disabled:opacity-50"
                        title="Delete email"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-[#EAE3D5] text-xs font-bold text-zinc-600">
          <span>
            Page {page + 1} of {totalPages} — showing {pageEmails.length} of {totalEmailCount} total
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0 || loadingPage}
              className="px-3 py-1.5 rounded-xl bg-[#EFE9DE] hover:bg-[#E4DCCF] disabled:opacity-40 disabled:cursor-not-allowed transition-all"
            >
              Previous
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1 || loadingPage}
              className="px-3 py-1.5 rounded-xl bg-[#EFE9DE] hover:bg-[#E4DCCF] disabled:opacity-40 disabled:cursor-not-allowed transition-all"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </Layout>
  );
}