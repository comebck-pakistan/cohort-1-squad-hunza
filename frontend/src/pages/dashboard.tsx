import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import Layout from '../components/Layout';
import { useRouter } from 'next/router';
import { supabase } from '../lib/supabase';
import { useAppState } from '../context/AppStateContext';
import { apiService } from '../lib/api';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from 'recharts';
import {
  Mail,
  FileCheck,
  UserPlus,
  ShieldAlert,
  ArrowUpRight,
  ChevronRight,
  Sparkles,
  TrendingUp,
} from 'lucide-react';

export default function Dashboard() {
  const router = useRouter();
  const [session, setSession] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const { emails, candidates, totalEmailCount } = useAppState();
  type PeriodOption = 'today' | '7days' | '30days' | 'custom';
const [timeRange, setTimeRange] = useState<PeriodOption>('7days');
const [customStart, setCustomStart] = useState<string>('');
const [customEnd, setCustomEnd] = useState<string>('');
const [showCustomPicker, setShowCustomPicker] = useState(false);
const [periodCount, setPeriodCount] = useState<number | null>(null);
const [periodCountLoading, setPeriodCountLoading] = useState(false);

const getPeriodRange = (period: PeriodOption): { start?: string; end?: string } => {
  const now = new Date();
  const endOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59);

  if (period === 'today') {
    const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0);
    return { start: startOfToday.toISOString(), end: endOfToday.toISOString() };
  }
  if (period === '7days') {
    const start = new Date(now);
    start.setDate(start.getDate() - 6);
    start.setHours(0, 0, 0, 0);
    return { start: start.toISOString(), end: endOfToday.toISOString() };
  }
  if (period === '30days') {
    const start = new Date(now);
    start.setDate(start.getDate() - 29);
    start.setHours(0, 0, 0, 0);
    return { start: start.toISOString(), end: endOfToday.toISOString() };
  }
  if (period === 'custom' && customStart && customEnd) {
    return {
      start: new Date(customStart).toISOString(),
      end: new Date(new Date(customEnd).setHours(23, 59, 59)).toISOString(),
    };
  }
  return {};
};

useEffect(() => {
  const fetchPeriodCount = async () => {
    if (timeRange === 'custom' && (!customStart || !customEnd)) {
      setPeriodCount(null);
      return;
    }
    setPeriodCountLoading(true);
    try {
      const { start, end } = getPeriodRange(timeRange);
      const count = await apiService.getEmailCount(start, end);
      setPeriodCount(count);
    } catch (err) {
      console.error('Failed to fetch period count', err);
      setPeriodCount(null);
    } finally {
      setPeriodCountLoading(false);
    }
  };
  fetchPeriodCount();
}, [timeRange, customStart, customEnd]);

const periodLabel = {
  today: 'Today',
  '7days': 'Last 7 Days',
  '30days': 'Last 30 Days',
  custom: customStart && customEnd ? `${customStart} → ${customEnd}` : 'Custom Range',
}[timeRange];

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setLoading(false);
      if (!session) router.push('/login');
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      if (!session) router.push('/login');
    });

    return () => subscription.unsubscribe();
  }, [router]);

  const activeChartData = useMemo(() => {
    const normalized = emails.map((email) => ({
      receivedAt: email.receivedAtRaw ? new Date(email.receivedAtRaw) : new Date(),
      category: email.category || 'General Inquiry',
    }));

    const dateBuckets: Record<string, { Applicants: number; Interviews: number; Inquiries: number; Spam: number }> = {};
    const today = new Date();

    const bucketLabel = (date: Date) => {
      if (timeRange === 'today') {
        return `${date.getHours()}:00`;
      }
      if (timeRange === '7days' || timeRange === 'custom') {
        return date.toLocaleDateString('en-US', { weekday: 'short' });
      }
      const weekNumber = Math.floor((date.getDate() - 1) / 7) + 1;
      return `W${weekNumber}`;
    };

    normalized.forEach((item) => {
      const label = bucketLabel(item.receivedAt);
      dateBuckets[label] ??= { Applicants: 0, Interviews: 0, Inquiries: 0, Spam: 0 };
      if (item.category === 'New Applicant') {
        dateBuckets[label].Applicants += 1;
      } else if (item.category === 'Interview Scheduling' || item.category === 'Interview Reschedule') {
        dateBuckets[label].Interviews += 1;
      } else if (item.category === 'Spam') {
        dateBuckets[label].Spam += 1;
      } else {
        dateBuckets[label].Inquiries += 1;
      }
    });

    const labels = timeRange === '30days'
      ? ['W1', 'W2', 'W3', 'W4']
      : timeRange === 'today'
      ? Array.from({ length: 24 }, (_, i) => `${i}:00`)
      : ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

    return labels.map((label) => ({
      day: label,
      Applicants: dateBuckets[label]?.Applicants ?? 0,
      Interviews: dateBuckets[label]?.Interviews ?? 0,
      Inquiries: dateBuckets[label]?.Inquiries ?? 0,
      Spam: dateBuckets[label]?.Spam ?? 0,
    }));
  }, [emails, timeRange]);

  const emailsTodayCount = totalEmailCount;
  const pendingDrafts = emails.filter((e) => e.draftReply && e.draftReply.status === 'pending');
  const newApplicantsCount = candidates.length;
  const spamFilteredCount = emails.filter((e) => e.category === 'Spam').length;

  const needsAttentionEmails = emails.filter(
    (e) => e.priority === 'High' && e.status !== 'Approved & Sent'
  );

  if (loading) return <div>Loading...</div>;
  if (!session) return null;

  return (
    <Layout>
      {/* Top Welcome Header - Original Warm Champagne / Beige Nixtio Style */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-zinc-900 tracking-tight">
            Welcome in, {session?.user?.user_metadata?.full_name || session?.user?.user_metadata?.name || 'User'} <span className="text-amber-500 font-normal">👋</span>
          </h1>
          <p className="text-xs text-zinc-500 font-semibold mt-1">
            Recruitment inbox analytics & pending AI draft approvals for {session?.user?.user_metadata?.full_name || session?.user?.user_metadata?.name || 'User'}
          </p>
        </div>
      </div>

      {/* Top Row — 4 Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Card 1 — Emails Today */}
        <div className="nixtio-card p-5 flex flex-col justify-between relative overflow-hidden group hover:border-zinc-400 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-zinc-500 uppercase tracking-wider">Total Emails</span>
            <div className="w-9 h-9 rounded-2xl bg-amber-400/20 text-amber-900 flex items-center justify-center font-bold">
              <Mail className="w-4 h-4 text-amber-800" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline justify-between">
            <span className="text-3xl font-extrabold text-zinc-900">{emailsTodayCount}</span>
            <span className="text-xs font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full flex items-center gap-0.5">
              <TrendingUp className="w-3 h-3" />
            </span>
          </div>
        </div>

        {/* Card 2 — Pending Drafts */}
        <div className="nixtio-card p-5 flex flex-col justify-between relative overflow-hidden group hover:border-zinc-400 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-zinc-500 uppercase tracking-wider">Pending Drafts</span>
            <div className="w-9 h-9 rounded-2xl bg-amber-400 text-zinc-900 flex items-center justify-center font-bold shadow-xs">
              <FileCheck className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline justify-between">
            <span className="text-3xl font-extrabold text-zinc-900">{pendingDrafts.length}</span>
            <Link
              href="/drafts"
              className="text-xs font-bold text-zinc-800 hover:text-amber-600 flex items-center gap-1"
            >
              Review queue <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>

        {/* Card 3 — New Applicants */}
        <Link
          href="/candidates"
          className="nixtio-card p-5 flex flex-col justify-between relative overflow-hidden group hover:border-zinc-400 transition-all cursor-pointer"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-zinc-500 uppercase tracking-wider">New Applicants</span>
            <div className="w-9 h-9 rounded-2xl bg-amber-400/20 text-amber-900 flex items-center justify-center font-bold">
              <UserPlus className="w-4 h-4 text-amber-800" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline justify-between">
            <span className="text-3xl font-extrabold text-zinc-900">{newApplicantsCount}</span>
            <span className="text-xs font-bold text-amber-900 bg-amber-100 px-2 py-0.5 rounded-full" />
          </div>
        </Link>

        {/* Card 4 — Spam Filtered */}
        <div className="nixtio-card p-5 flex flex-col justify-between relative overflow-hidden group hover:border-zinc-400 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-zinc-500 uppercase tracking-wider">Spam Filtered</span>
            <div className="w-9 h-9 rounded-2xl bg-rose-100 text-rose-800 flex items-center justify-center font-bold">
              <ShieldAlert className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline justify-between">
            <span className="text-3xl font-extrabold text-zinc-900">{spamFilteredCount}</span>
            <span className="text-[11px] font-bold text-zinc-400">100% blocked</span>
          </div>
        </div>
      </div>

      {/* Middle Row — Email Volume Chart */}
      <div className="nixtio-card p-6 space-y-4">
        <div className="flex flex-col gap-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-extrabold text-zinc-900">
                {periodLabel} — Email Volume & Category Breakdown
              </h2>
              <p className="text-xs text-zinc-500 font-medium flex items-center gap-2">
                <span>Recruiter messages categorized by AI</span>
                <span className="inline-flex items-center gap-1 bg-amber-100 text-amber-900 font-bold px-2 py-0.5 rounded-full text-[11px]">
                  {periodCountLoading ? '...' : periodCount !== null ? `${periodCount} emails` : '—'}
                </span>
              </p>
            </div>

            <div className="flex items-center gap-2 bg-[#EFE9DE] p-1 rounded-xl text-xs font-bold text-zinc-700 flex-wrap">
              <button
                onClick={() => { setTimeRange('today'); setShowCustomPicker(false); }}
                className={`px-3 py-1 rounded-lg transition-all cursor-pointer ${
                  timeRange === 'today' ? 'bg-zinc-900 text-white shadow-xs' : 'hover:text-zinc-900'
                }`}
              >
                Today
              </button>
              <button
                onClick={() => { setTimeRange('7days'); setShowCustomPicker(false); }}
                className={`px-3 py-1 rounded-lg transition-all cursor-pointer ${
                  timeRange === '7days' ? 'bg-zinc-900 text-white shadow-xs' : 'hover:text-zinc-900'
                }`}
              >
                Last 7 Days
              </button>
              <button
                onClick={() => { setTimeRange('30days'); setShowCustomPicker(false); }}
                className={`px-3 py-1 rounded-lg transition-all cursor-pointer ${
                  timeRange === '30days' ? 'bg-zinc-900 text-white shadow-xs' : 'hover:text-zinc-900'
                }`}
              >
                Last 30 Days
              </button>
              <button
                onClick={() => { setTimeRange('custom'); setShowCustomPicker((v) => !v); }}
                className={`px-3 py-1 rounded-lg transition-all cursor-pointer ${
                  timeRange === 'custom' ? 'bg-zinc-900 text-white shadow-xs' : 'hover:text-zinc-900'
                }`}
              >
                Custom
              </button>
            </div>
          </div>

          {showCustomPicker && (
            <div className="flex flex-wrap items-center gap-3 bg-[#EFE9DE]/60 border border-[#E4DCCF] p-3 rounded-2xl text-xs font-bold text-zinc-700">
              <label className="flex items-center gap-2">
                From
                <input
                  type="date"
                  value={customStart}
                  onChange={(e) => setCustomStart(e.target.value)}
                  className="bg-white border border-[#E4DCCF] rounded-lg px-2 py-1 text-xs font-medium"
                />
              </label>
              <label className="flex items-center gap-2">
                To
                <input
                  type="date"
                  value={customEnd}
                  onChange={(e) => setCustomEnd(e.target.value)}
                  className="bg-white border border-[#E4DCCF] rounded-lg px-2 py-1 text-xs font-medium"
                />
              </label>
              {!customStart || !customEnd ? (
                <span className="text-zinc-400 font-medium">Select both dates to see the count</span>
              ) : null}
            </div>
          )}
        </div>

        <div className="h-64 w-full pt-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={activeChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E8E2D6" />
              <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fill: '#71717A', fontSize: 12 }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fill: '#71717A', fontSize: 12 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1E1E24',
                  borderColor: '#272730',
                  borderRadius: '12px',
                  color: '#FFF',
                  fontSize: '12px',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
              <Bar dataKey="Applicants" fill="#1E1E24" radius={[6, 6, 0, 0]} />
              <Bar dataKey="Interviews" fill="#F5C842" radius={[6, 6, 0, 0]} />
              <Bar dataKey="Inquiries" fill="#8C8C9A" radius={[6, 6, 0, 0]} />
              <Bar dataKey="Spam" fill="#F43F5E" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Bottom Row — Two Panels Side by Side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Panel — Needs Attention */}
        <div className="nixtio-card p-6 space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-rose-500 animate-pulse"></div>
                <h3 className="text-base font-extrabold text-zinc-900">Needs Attention</h3>
              </div>
              <span className="text-xs font-bold text-rose-800 bg-rose-100 px-2.5 py-0.5 rounded-full">
                {needsAttentionEmails.length} High Priority
              </span>
            </div>

            <div className="space-y-3">
              {needsAttentionEmails.map((email) => (
                <Link
                  key={email.id}
                  href={`/inbox/${email.id}`}
                  className="block p-4 rounded-2xl bg-[#EFE9DE]/60 border border-[#E8E1D2] hover:bg-[#E8E1D2] transition-all group"
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-extrabold text-zinc-900">{email.senderName}</span>
                    <span className="text-[10px] font-extrabold text-rose-700 bg-rose-100 border border-rose-200 px-2 py-0.5 rounded-full">
                      🔴 High Priority
                    </span>
                  </div>
                  <p className="text-xs font-semibold text-zinc-800 line-clamp-1 group-hover:text-amber-800">
                    {email.subject}
                  </p>
                  <div className="flex items-center justify-between mt-2 text-[11px] text-zinc-500 font-medium">
                    <span className="bg-zinc-200 text-zinc-700 px-2 py-0.5 rounded-md text-[10px] font-bold">
                      {email.category}
                    </span>
                    <span>{email.date}</span>
                  </div>
                </Link>
              ))}
            </div>
          </div>

          <Link
            href="/inbox"
            className="inline-flex items-center justify-center gap-1.5 text-xs font-bold text-zinc-700 hover:text-zinc-900 pt-4 border-t border-[#EAE3D5]"
          >
            View all inbox emails <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* Right Panel — Recent Drafts */}
        <div className="nixtio-card p-6 space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-amber-500" />
                <h3 className="text-base font-extrabold text-zinc-900">Recent Drafts Awaiting Approval</h3>
              </div>
              <span className="text-xs font-bold text-amber-900 bg-amber-200 px-2.5 py-0.5 rounded-full">
                {pendingDrafts.length} Pending
              </span>
            </div>

            <div className="space-y-3">
              {pendingDrafts.slice(0, 3).map((email) => (
                <div
                  key={email.id}
                  className="p-4 rounded-2xl bg-[#EFE9DE]/60 border border-[#E8E1D2] flex items-center justify-between gap-4"
                >
                  <div className="min-w-0 space-y-1">
                    <p className="text-xs font-extrabold text-zinc-900 truncate">{email.senderName}</p>
                    <p className="text-xs font-medium text-zinc-600 truncate">{email.subject}</p>
                  </div>
                  <Link
                    href={`/inbox/${email.id}`}
                    className="shrink-0 bg-zinc-900 hover:bg-zinc-800 text-white text-xs font-bold px-3.5 py-2 rounded-xl transition-all shadow-sm flex items-center gap-1"
                  >
                    <span>Review</span>
                    <ArrowUpRight className="w-3.5 h-3.5 text-amber-400" />
                  </Link>
                </div>
              ))}
            </div>
          </div>

          <Link
            href="/drafts"
            className="inline-flex items-center justify-center gap-1.5 text-xs font-bold text-zinc-700 hover:text-zinc-900 pt-4 border-t border-[#EAE3D5]"
          >
            Launch Draft Approval Queue <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>
    </Layout>
  );
}
