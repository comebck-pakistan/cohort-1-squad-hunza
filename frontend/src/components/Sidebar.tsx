import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import {
  LayoutDashboard,
  Inbox,
  FileCheck,
  Users,
  MessageSquare,
  History,
  Settings,
  LogOut,
  Sparkles,
  ChevronRight,
  ShieldCheck,
} from 'lucide-react';
import { useAppState } from '../context/AppStateContext';

export default function Sidebar() {
  const router = useRouter();
  const { emails, isGmailConnected } = useAppState();

  const pendingDraftsCount = emails.filter((e) => e.draftReply && e.draftReply.status === 'pending').length;
  const highPriorityCount = emails.filter((e) => e.priority === 'High' && e.status !== 'Approved & Sent').length;

  const navItems = [
    { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { label: 'Inbox', href: '/inbox', icon: Inbox, badge: emails.length },
    { label: 'Drafts', href: '/drafts', icon: FileCheck, badge: pendingDraftsCount, badgeColor: 'bg-amber-400 text-zinc-900 font-bold' },
    { label: 'Candidates', href: '/candidates', icon: Users },
    { label: 'AI Chat', href: '/chat', icon: MessageSquare, isSparkle: true },
    { label: 'Activity Log', href: '/activity', icon: History },
    { label: 'Settings', href: '/settings', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-[#FBF9F5]/90 backdrop-blur-md border-r border-[#EAE3D5] flex flex-col justify-between p-5 min-h-screen shrink-0 shadow-sm">
      <div>
        {/* Brand Header */}
        <div className="flex items-center gap-3 px-2 py-3 mb-6">
          <div className="w-10 h-10 rounded-2xl bg-zinc-900 text-amber-400 flex items-center justify-center font-extrabold text-xl shadow-md">
            S
          </div>
          <div>
            <h1 className="font-extrabold text-lg tracking-tight text-zinc-900">Sortdesk HR</h1>
            <p className="text-xs text-zinc-500 font-medium flex items-center gap-1">
              <span className={`w-2 h-2 rounded-full ${isGmailConnected ? 'bg-emerald-500' : 'bg-rose-500'}`}></span>
              {isGmailConnected ? 'Gmail Sync Active' : 'Gmail Disconnected'}
            </p>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = router.pathname === item.href || (item.href !== '/dashboard' && router.pathname.startsWith(item.href));

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center justify-between px-3.5 py-2.5 rounded-2xl font-semibold text-sm transition-all duration-200 ${
                  isActive
                    ? 'bg-zinc-900 text-white shadow-md shadow-zinc-900/10'
                    : 'text-zinc-600 hover:bg-[#F3EDDF] hover:text-zinc-900'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-amber-400' : 'text-zinc-500'}`} />
                  <span>{item.label}</span>
                  {item.isSparkle && (
                    <Sparkles className="w-3.5 h-3.5 text-amber-500 animate-pulse" />
                  )}
                </div>
                {item.badge !== undefined && item.badge > 0 && (
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full font-bold ${
                      item.badgeColor || (isActive ? 'bg-amber-400 text-zinc-900' : 'bg-zinc-200 text-zinc-700')
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Bottom User & Helper Card */}
      <div className="space-y-4 pt-4 border-t border-[#EAE3D5]">
        {/* Onboarding helper card */}
        <div className="bg-gradient-to-br from-zinc-900 to-zinc-800 text-white p-4 rounded-2xl shadow-nixtio">
          <div className="flex items-center gap-2 mb-1.5">
            <ShieldCheck className="w-4 h-4 text-amber-400" />
            <span className="text-xs font-bold tracking-wide uppercase text-amber-300">AI Assistant</span>
          </div>
          <p className="text-xs text-zinc-300 mb-3 leading-relaxed">
            Auto-classifying candidates & drafting personalized replies.
          </p>
          <Link
            href="/onboarding"
            className="inline-flex items-center gap-1 text-xs text-amber-300 hover:text-amber-200 font-bold"
          >
            Update AI Persona <ChevronRight className="w-3 h-3" />
          </Link>
        </div>

        {/* User Card */}
        <div className="flex items-center justify-between px-2">
          <div className="flex items-center gap-2.5">
            <img
              src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80"
              alt="Sarah Jenkins"
              className="w-9 h-9 rounded-full object-cover border-2 border-amber-300 shadow-sm"
            />
            <div>
              <p className="text-xs font-bold text-zinc-900">
                {emails[0]?.userEmail || 'Connected User'}
              </p>
              <p className="text-[10px] text-zinc-500 font-medium">Head of Recruiting</p>
            </div>
            
          </div>
          <button
            onClick={() => router.push('/login')}
            title="Sign out"
            className="p-1.5 text-zinc-400 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
