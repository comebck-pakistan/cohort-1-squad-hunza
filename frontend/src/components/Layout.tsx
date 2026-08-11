import React from 'react';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import ResumeModal from './ResumeModal';
import Toast from './Toast';

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen bg-[#EFE9DE]">
      {/* Left Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <TopBar />
        <main className="flex-1 p-6 md:p-8 max-w-7xl w-full mx-auto space-y-8 overflow-y-auto">
          {children}
        </main>
      </div>

      {/* Overlay Modals & Toast Notifications */}
      <ResumeModal />
      <Toast />
    </div>
  );
}
