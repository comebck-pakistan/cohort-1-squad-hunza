import React, { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import {
  Bell,
  Search,
  Sparkles,
  SlidersHorizontal,
  LogOut,
  User,
  CheckCircle2,
  Mail,
  ShieldCheck,
  X,
  FileCheck,
  ChevronRight,
  UserPlus,
} from 'lucide-react';
import { useAppState } from '../context/AppStateContext';

export default function TopBar() {
  const router = useRouter();
  const { emails, candidates, isGmailConnected, setGmailConnected, showToast } = useAppState();

  const pendingDraftsCount = emails.filter((e) => e.draftReply && e.draftReply.status === 'pending').length;

  // Dropdown visibility states for top right buttons
  const [showNotifications, setShowNotifications] = useState(false);
  const [showQuickSettings, setShowQuickSettings] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [unreadCount, setUnreadCount] = useState(pendingDraftsCount + 1);

  const topNavLinks: Array<{ label: string; href: string; badge?: number }> = [
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'Inbox', href: '/inbox' },
    { label: 'Drafts', href: '/drafts', badge: pendingDraftsCount },
    { label: 'Candidates', href: '/candidates' },
    { label: 'AI Chat', href: '/chat' },
    { label: 'Activity', href: '/activity' },
    { label: 'Setting', href: '/settings' },
  ];

  const handleMarkAllRead = () => {
    setUnreadCount(0);
    showToast('Notifications marked as read');
  };

  return (
    <header className="w-full bg-[#FBF9F5]/80 backdrop-blur-lg border-b border-[#EAE3D5] px-6 py-3.5 flex items-center justify-between sticky top-0 z-30 shadow-xs">
      {/* Brand logo pill - Rebranded to Sortdesk */}
      <div className="flex items-center gap-3">
        <Link
          href="/dashboard"
          className="flex items-center gap-2 bg-[#EFE9DE] border border-[#EAE3D5] px-4 py-1.5 rounded-full hover:border-zinc-400 transition-all"
        >
          <span className="font-extrabold text-base tracking-tight text-zinc-900">Sortdesk</span>
          <span className="w-2 h-2 rounded-full bg-amber-400"></span>
        </Link>
      </div>

      {/* Horizontal pill navigation bar */}
      <nav className="hidden md:flex items-center bg-[#EFE9DE]/90 border border-[#E8E1D2] p-1 rounded-full shadow-inner">
        {topNavLinks.map((link: { label: string; href: string; badge?: number }) => {
          const isActive =
            router.pathname === link.href || (link.href !== '/dashboard' && router.pathname.startsWith(link.href));
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all duration-200 flex items-center gap-1.5 ${
                isActive
                  ? 'bg-zinc-900 text-white shadow-md'
                  : 'text-zinc-600 hover:text-zinc-900 hover:bg-[#E4DCCF]'
              }`}
            >
              <span>{link.label}</span>
              {link.badge !== undefined && link.badge > 0 && (
                <span
                  className={`text-[10px] px-1.5 py-0.2 rounded-full font-extrabold ${
                    isActive ? 'bg-amber-400 text-zinc-900' : 'bg-zinc-300 text-zinc-800'
                  }`}
                >
                  {link.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Right control action icons - Now 100% Functional! */}
      <div className="flex items-center gap-2.5 relative">
        {/* 1. Ask AI Button */}
        <button
          onClick={() => router.push('/chat')}
          className="hidden sm:flex items-center gap-1.5 bg-amber-400/20 text-amber-900 border border-amber-300 px-3 py-1.5 rounded-full text-xs font-bold hover:bg-amber-400/30 transition-all cursor-pointer"
        >
          <Sparkles className="w-3.5 h-3.5 text-amber-600 animate-pulse" />
          <span>Ask AI</span>
        </button>

        {/* 2. Notifications Bell Button */}
        <div className="relative">
          <button
            onClick={() => {
              setShowNotifications(!showNotifications);
              setShowQuickSettings(false);
              setShowProfileMenu(false);
            }}
            title="Notifications"
            className="w-9 h-9 rounded-full bg-[#EFE9DE] border border-[#EAE3D5] flex items-center justify-center text-zinc-600 hover:text-zinc-900 hover:bg-[#E4DCCF] transition-all relative cursor-pointer"
          >
            <Bell className="w-4 h-4" />
            {unreadCount > 0 && (
              <span className="absolute top-1 right-1 w-2.5 h-2.5 rounded-full bg-amber-500 ring-2 ring-white"></span>
            )}
          </button>

          {/* Notifications Dropdown Panel */}
          {showNotifications && (
            <div className="absolute right-0 mt-3 w-80 bg-[#FBF9F5] border border-[#EAE3D5] rounded-3xl shadow-nixtio-lg p-4 space-y-3 z-50 animate-fadeIn">
              <div className="flex items-center justify-between border-b border-[#EAE3D5] pb-2">
                <div className="flex items-center gap-2">
                  <Bell className="w-4 h-4 text-amber-500" />
                  <span className="font-extrabold text-xs text-zinc-900">Notifications</span>
                  {unreadCount > 0 && (
                    <span className="text-[10px] bg-amber-400 text-zinc-950 font-bold px-1.5 py-0.2 rounded-full">
                      {unreadCount}
                    </span>
                  )}
                </div>
                <button
                  onClick={handleMarkAllRead}
                  className="text-[11px] font-bold text-amber-800 hover:text-amber-950 cursor-pointer"
                >
                  Mark read
                </button>
              </div>

              <div className="space-y-2 max-h-64 overflow-y-auto">
                <Link
                  href="/drafts"
                  onClick={() => setShowNotifications(false)}
                  className="block p-3 rounded-2xl bg-[#EFE9DE]/70 border border-[#E8E1D2] hover:bg-[#E4DCCF] transition-all space-y-1"
                >
                  <div className="flex items-center justify-between text-xs font-bold text-zinc-900">
                    <span className="flex items-center gap-1.5">
                      <FileCheck className="w-3.5 h-3.5 text-amber-600" /> Pending AI Drafts
                    </span>
                    <span className="text-[10px] font-mono text-zinc-400">Just now</span>
                  </div>
                  <p className="text-[11px] text-zinc-600 font-medium">
                    {pendingDraftsCount} drafts ready for approval in your queue.
                  </p>
                </Link>

                <Link
                  href="/candidates"
                  onClick={() => setShowNotifications(false)}
                  className="block p-3 rounded-2xl bg-[#EFE9DE]/70 border border-[#E8E1D2] hover:bg-[#E4DCCF] transition-all space-y-1"
                >
                  <div className="flex items-center justify-between text-xs font-bold text-zinc-900">
                    <span className="flex items-center gap-1.5">
                      <UserPlus className="w-3.5 h-3.5 text-emerald-600" /> New Candidate
                    </span>
                    <span className="text-[10px] font-mono text-zinc-400">10m ago</span>
                  </div>
                  <p className="text-[11px] text-zinc-600 font-medium">
                    John Smith applied for AI Engineer position with resume.
                  </p>
                </Link>
              </div>

              <div className="pt-2 border-t border-[#EAE3D5] text-center">
                <Link
                  href="/inbox"
                  onClick={() => setShowNotifications(false)}
                  className="text-xs font-bold text-zinc-700 hover:text-zinc-900 inline-flex items-center gap-1"
                >
                  View all in inbox <ChevronRight className="w-3 h-3" />
                </Link>
              </div>
            </div>
          )}
        </div>

        {/* 3. Quick Settings / Sliders Button */}
        <div className="relative">
          <button
            onClick={() => {
              setShowQuickSettings(!showQuickSettings);
              setShowNotifications(false);
              setShowProfileMenu(false);
            }}
            title="Quick Preferences"
            className="w-9 h-9 rounded-full bg-[#EFE9DE] border border-[#EAE3D5] flex items-center justify-center text-zinc-600 hover:text-zinc-900 hover:bg-[#E4DCCF] transition-all cursor-pointer"
          >
            <SlidersHorizontal className="w-4 h-4" />
          </button>

          {/* Quick Settings Dropdown Panel */}
          {showQuickSettings && (
            <div className="absolute right-0 mt-3 w-72 bg-[#FBF9F5] border border-[#EAE3D5] rounded-3xl shadow-nixtio-lg p-4 space-y-3 z-50 animate-fadeIn">
              <div className="flex items-center justify-between border-b border-[#EAE3D5] pb-2">
                <span className="font-extrabold text-xs text-zinc-900">Quick Controls</span>
                <button
                  onClick={() => setShowQuickSettings(false)}
                  className="text-zinc-400 hover:text-zinc-900"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>

              <div className="space-y-3 text-xs">
                <div className="flex items-center justify-between p-2.5 bg-[#EFE9DE]/70 rounded-xl">
                  <span className="font-bold text-zinc-800">Gmail Connection</span>
                  <button
                    onClick={() => {
                      setGmailConnected(!isGmailConnected);
                      showToast(isGmailConnected ? 'Gmail disconnected' : 'Gmail connected');
                    }}
                    className={`px-2.5 py-1 rounded-lg text-[10px] font-extrabold ${
                      isGmailConnected ? 'bg-emerald-600 text-white' : 'bg-rose-600 text-white'
                    }`}
                  >
                    {isGmailConnected ? 'Connected' : 'Reconnect'}
                  </button>
                </div>

                <Link
                  href="/settings"
                  onClick={() => setShowQuickSettings(false)}
                  className="block w-full text-center bg-zinc-900 text-white font-bold py-2 rounded-xl text-xs hover:bg-zinc-800 transition-all"
                >
                  Open Full Settings
                </Link>
              </div>
            </div>
          )}
        </div>

        {/* 4. Profile Avatar & User Dropdown */}
        <div className="relative">
          <button
            onClick={() => {
              setShowProfileMenu(!showProfileMenu);
              setShowNotifications(false);
              setShowQuickSettings(false);
            }}
            title="Profile Menu"
            className="w-9 h-9 rounded-full border-2 border-amber-400 overflow-hidden shadow-xs hover:ring-2 hover:ring-amber-300 transition-all cursor-pointer block"
          >
            <img
              src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80"
              alt="User Profile"
              className="w-full h-full object-cover"
            />
          </button>

          {/* Profile Dropdown Panel */}
          {showProfileMenu && (
            <div className="absolute right-0 mt-3 w-64 bg-[#FBF9F5] border border-[#EAE3D5] rounded-3xl shadow-nixtio-lg p-4 space-y-3 z-50 animate-fadeIn">
              <div className="flex items-center gap-3 border-b border-[#EAE3D5] pb-3">
                <img
                  src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80"
                  alt="Sarah Jenkins"
                  className="w-10 h-10 rounded-full object-cover border border-amber-400"
                />
                <div>
                  <p className="font-extrabold text-xs text-zinc-900">Sarah Jenkins</p>
                  <p className="text-[10px] text-zinc-500 font-medium">Head of Recruiting</p>
                  <p className="text-[9px] text-zinc-400 font-mono">sarah@sortdesk.hr</p>
                </div>
              </div>

              <div className="space-y-1">
                <Link
                  href="/settings"
                  onClick={() => setShowProfileMenu(false)}
                  className="flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-bold text-zinc-700 hover:bg-[#EFE9DE] hover:text-zinc-900"
                >
                  <SlidersHorizontal className="w-3.5 h-3.5" /> Account Settings
                </Link>
                <Link
                  href="/onboarding"
                  onClick={() => setShowProfileMenu(false)}
                  className="flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-bold text-zinc-700 hover:bg-[#EFE9DE] hover:text-zinc-900"
                >
                  <Sparkles className="w-3.5 h-3.5 text-amber-500" /> AI Persona Setup
                </Link>
              </div>

              <div className="pt-2 border-t border-[#EAE3D5]">
                <button
                  onClick={() => router.push('/login')}
                  className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl text-xs font-bold text-rose-700 hover:bg-rose-50 cursor-pointer"
                >
                  <LogOut className="w-3.5 h-3.5" /> Sign Out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
