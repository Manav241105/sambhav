import React from 'react';
import Sidebar from '../components/Sidebar';

/**
 * Shared wrapper for all dashboard pages.
 * Renders the Sidebar + a right-side content area.
 */
export default function DashboardLayout({ title, children }) {
  return (
    <div className="flex min-h-screen bg-[#f4f5f0] dark:bg-[#0b0f19] transition-colors">
      <Sidebar />

      {/* Main content — offset by sidebar width */}
      <main className="flex-1 ml-[256px] p-8">
        <h1 className="text-2xl font-extrabold text-gray-900 dark:text-white mb-6">
          {title}
        </h1>
        {children}
      </main>
    </div>
  );
}
