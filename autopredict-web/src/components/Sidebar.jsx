import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard,
  Truck,
  CalendarDays,
  MessageSquare,
  BarChart3,
  ShieldCheck,
  Settings2,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Bell,
  Search,
  FileText,
  RotateCcw,
  AlertTriangle,
  X,
  Clock,
} from 'lucide-react';
import ThemeToggle from './ThemeToggle';

const spring = { type: 'spring', stiffness: 100, damping: 10 };

const NAV_ITEMS = {
  ops: [
    { to: '/dashboard/operations', end: true, icon: LayoutDashboard, label: 'Overview' },
    { to: '/dashboard/operations/fleet', icon: Truck, label: 'Fleet' },
    { to: '/dashboard/operations/calendar', icon: CalendarDays, label: 'Bay Calendar' },
    { to: '/dashboard/operations/conversations', icon: MessageSquare, label: 'Conversations' },
    { to: '/dashboard/recalls', icon: RotateCcw, label: 'Recalls' },
  ],
  manager: [
    { to: '/dashboard/manager', end: true, icon: LayoutDashboard, label: 'Overview' },
    { to: '/dashboard/manager/escalations', icon: ShieldCheck, label: 'Escalations' },
    { to: '/dashboard/manager/revenue', icon: BarChart3, label: 'Revenue' },
    { to: '/dashboard/manager/workload', icon: MessageSquare, label: 'Workload' },
    { to: '/dashboard/reports', icon: FileText, label: 'Reports' },
  ],
  executive: [
    { to: '/dashboard/executive', end: true, icon: LayoutDashboard, label: 'Overview' },
    { to: '/dashboard/executive/fleet-health', icon: Truck, label: 'Fleet Health' },
    { to: '/dashboard/executive/trends', icon: BarChart3, label: 'Trends' },
    { to: '/dashboard/executive/recalls', icon: RotateCcw, label: 'Recalls' },
    { to: '/dashboard/reports', icon: FileText, label: 'Reports' },
    { to: '/dashboard/settings', icon: Settings2, label: 'Settings' },
  ],
};

const ROLE_LABELS = { ops: 'Operations', manager: 'Manager', executive: 'Executive' };

/* ── Mock notification data ────────────────────────── */
const MOCK_NOTIFICATIONS = [
  { id: 1, priority: 'P0', vehicle: 'VEH003', message: 'Critical brake failure risk', time: '2 min ago', read: false },
  { id: 2, priority: 'P1', vehicle: 'VEH007', message: 'Battery voltage below threshold', time: '18 min ago', read: false },
  { id: 3, priority: 'P0', vehicle: 'VEH001', message: 'Coolant system critical', time: '45 min ago', read: true },
  { id: 4, priority: 'P2', vehicle: 'VEH009', message: 'Tire pressure warning — FL', time: '1h ago', read: true },
  { id: 5, priority: 'P1', vehicle: 'VEH002', message: 'Oil pressure dropping', time: '2h ago', read: true },
];

export default function Sidebar({ onCollapseChange }) {
  const navigate = useNavigate();
  const role = localStorage.getItem('ap_role') || 'ops';
  const email = (() => {
    try {
      const t = localStorage.getItem('ap_token');
      if (!t) return 'user@autopredict.io';
      return JSON.parse(atob(t)).email || 'user@autopredict.io';
    } catch { return 'user@autopredict.io'; }
  })();
  const items = NAV_ITEMS[role] || NAV_ITEMS.ops;
  const [collapsed, setCollapsed] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [notifications, setNotifications] = useState(MOCK_NOTIFICATIONS);

  const unreadCount = notifications.filter((n) => !n.read).length;

  const handleCollapse = (val) => {
    setCollapsed(val);
    onCollapseChange?.(val);
  };

  const handleLogout = () => {
    localStorage.removeItem('ap_token');
    localStorage.removeItem('ap_role');
    navigate('/login');
  };

  const markAllRead = () => setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));

  return (
    <>
      {/* ── Sidebar ─────────────────────────────────── */}
      <motion.aside
        animate={{ width: collapsed ? 72 : 256 }}
        transition={spring}
        className="fixed top-0 left-0 z-40 flex flex-col h-screen border-r bg-white dark:bg-[#0b0f19] border-gray-200 dark:border-gray-800 overflow-hidden"
      >
        {/* Logo row */}
        <div className="flex items-center justify-between px-4 h-16 border-b border-gray-200 dark:border-gray-800 shrink-0">
          <AnimatePresence mode="wait">
            {!collapsed && (
              <motion.span
                key="logo"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="text-lg font-extrabold text-gray-900 dark:text-white whitespace-nowrap"
              >
                Auto<span className="text-[#6366f1]">Predict</span>
              </motion.span>
            )}
          </AnimatePresence>
          <button
            onClick={() => handleCollapse(!collapsed)}
            className="p-1.5 rounded-lg text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-white/5 transition-colors shrink-0"
          >
            {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
          </button>
        </div>

        {/* Role badge */}
        <AnimatePresence mode="wait">
          {!collapsed && (
            <motion.div
              key="role"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="px-4 py-2 shrink-0"
            >
              <span className="inline-block px-2.5 py-1 text-[10px] font-bold tracking-wider uppercase rounded-full bg-[#6366f1]/15 text-[#6366f1]">
                {ROLE_LABELS[role]}
              </span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Search button */}
        <div className="px-3 pb-1 shrink-0">
          <button
            onClick={() => setShowSearch(true)}
            className={`group flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm font-medium text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-white/5 transition-colors ${collapsed ? 'justify-center' : ''}`}
          >
            <Search size={18} className="shrink-0" />
            <AnimatePresence mode="wait">
              {!collapsed && (
                <motion.span
                  key="search-label"
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -8 }}
                  transition={{ duration: 0.15 }}
                  className="whitespace-nowrap flex-1 text-left"
                >
                  Search...
                </motion.span>
              )}
            </AnimatePresence>
            {!collapsed && (
              <span className="text-[9px] bg-gray-100 dark:bg-white/10 text-gray-400 px-1.5 py-0.5 rounded font-mono">⌘K</span>
            )}
          </button>
        </div>

        {/* Nav links */}
        <nav className="flex-1 px-3 py-2 space-y-1 overflow-y-auto">
          {items.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `group flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${isActive
                    ? 'bg-[#6366f1]/10 text-[#6366f1]'
                    : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-white/5'
                  } ${collapsed ? 'justify-center' : ''}`
                }
              >
                <Icon size={20} className="shrink-0" />
                <AnimatePresence mode="wait">
                  {!collapsed && (
                    <motion.span
                      key={item.label}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -8 }}
                      transition={{ duration: 0.15 }}
                      className="whitespace-nowrap"
                    >
                      {item.label}
                    </motion.span>
                  )}
                </AnimatePresence>
              </NavLink>
            );
          })}
        </nav>

        {/* Bottom section */}
        <div className="px-3 py-3 space-y-1 border-t border-gray-200 dark:border-gray-800 shrink-0">
          {/* Notifications */}
          <button
            onClick={() => setShowNotifications(true)}
            className={`relative group flex items-center gap-3 w-full px-3 py-2.5 text-sm font-medium text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-white/5 transition-colors rounded-xl ${collapsed ? 'justify-center' : ''}`}
          >
            <div className="relative shrink-0">
              <Bell size={20} />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 w-4 h-4 text-[9px] font-bold rounded-full bg-red-500 text-white flex items-center justify-center">
                  {unreadCount}
                </span>
              )}
            </div>
            <AnimatePresence mode="wait">
              {!collapsed && (
                <motion.span
                  key="notif-label"
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -8 }}
                  transition={{ duration: 0.15 }}
                  className="whitespace-nowrap flex-1 text-left"
                >
                  Notifications
                </motion.span>
              )}
            </AnimatePresence>
          </button>

          {/* Theme Toggle */}
          <div className={`flex items-center ${collapsed ? 'justify-center px-3' : 'px-3'}`}>
            <ThemeToggle />
          </div>

          {/* User profile */}
          <AnimatePresence mode="wait">
            {!collapsed && (
              <motion.div
                key="profile"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex items-center gap-3 px-3 py-2 rounded-xl bg-gray-50 dark:bg-white/[0.03] border border-gray-200 dark:border-gray-800"
              >
                <div className="w-7 h-7 rounded-lg bg-[#6366f1] flex items-center justify-center text-[10px] font-bold text-gray-900 shrink-0">
                  {email.slice(0, 2).toUpperCase()}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-bold text-gray-900 dark:text-white truncate">{ROLE_LABELS[role]}</p>
                  <p className="text-[10px] text-gray-400 dark:text-gray-500 truncate">{email}</p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Sign out */}
          <button
            onClick={handleLogout}
            className={`flex items-center w-full gap-3 px-3 py-2.5 text-sm font-medium text-gray-500 transition-colors rounded-xl hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/5 ${collapsed ? 'justify-center' : ''}`}
          >
            <LogOut size={20} className="shrink-0" />
            <AnimatePresence mode="wait">
              {!collapsed && (
                <motion.span
                  key="logout"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="whitespace-nowrap"
                >
                  Sign Out
                </motion.span>
              )}
            </AnimatePresence>
          </button>
        </div>
      </motion.aside>

      {/* ── Notification Panel ──────────────────────── */}
      <AnimatePresence>
        {showNotifications && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowNotifications(false)}
              className="fixed inset-0 z-50 bg-black/20 backdrop-blur-sm"
            />
            <motion.div
              initial={{ opacity: 0, x: -40 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -40 }}
              transition={spring}
              style={{ left: collapsed ? 72 : 256 }}
              className="fixed top-0 bottom-0 z-50 w-80 bg-white dark:bg-[#111827] border-r border-gray-200 dark:border-gray-700 shadow-2xl flex flex-col"
            >
              <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-700">
                <div>
                  <h3 className="text-sm font-extrabold text-gray-900 dark:text-white">Notifications</h3>
                  <p className="text-xs text-gray-400">{unreadCount} unread</p>
                </div>
                <div className="flex items-center gap-2">
                  {unreadCount > 0 && (
                    <button onClick={markAllRead} className="text-[10px] text-[#6366f1] font-bold hover:underline">
                      Mark all read
                    </button>
                  )}
                  <button onClick={() => setShowNotifications(false)} className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-white/5">
                    <X size={14} className="text-gray-400" />
                  </button>
                </div>
              </div>
              <div className="flex-1 overflow-y-auto divide-y divide-gray-100 dark:divide-white/5">
                {notifications.map((n) => (
                  <motion.div
                    key={n.id}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-white/[0.02] transition-colors ${!n.read ? 'bg-[#6366f1]/[0.03]' : ''}`}
                    onClick={() => setNotifications((prev) => prev.map((x) => x.id === n.id ? { ...x, read: true } : x))}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`mt-0.5 p-1.5 rounded-lg shrink-0 ${n.priority === 'P0' ? 'bg-red-500/15 text-red-500' : n.priority === 'P1' ? 'bg-orange-500/15 text-orange-500' : 'bg-amber-500/15 text-amber-500'}`}>
                        <AlertTriangle size={12} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-0.5">
                          <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full ${n.priority === 'P0' ? 'bg-red-500/15 text-red-500' : n.priority === 'P1' ? 'bg-orange-500/15 text-orange-500' : 'bg-amber-500/15 text-amber-500'}`}>
                            {n.priority}
                          </span>
                          <span className="text-[10px] font-bold text-gray-500 dark:text-gray-400">{n.vehicle}</span>
                          {!n.read && <span className="w-1.5 h-1.5 rounded-full bg-[#6366f1] ml-auto shrink-0" />}
                        </div>
                        <p className="text-xs text-gray-700 dark:text-gray-300 leading-relaxed">{n.message}</p>
                        <div className="flex items-center gap-1 mt-1">
                          <Clock size={9} className="text-gray-400" />
                          <span className="text-[9px] text-gray-400">{n.time}</span>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* ── Search Palette ──────────────────────────── */}
      <AnimatePresence>
        {showSearch && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => { setShowSearch(false); setSearchQuery(''); }}
              className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm"
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: -20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: -20 }}
              transition={spring}
              className="fixed top-24 left-1/2 -translate-x-1/2 z-50 w-full max-w-lg bg-white dark:bg-[#111827] border border-gray-200 dark:border-gray-700 rounded-2xl shadow-2xl overflow-hidden"
            >
              <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                <Search size={18} className="text-gray-400 shrink-0" />
                <input
                  autoFocus
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search vehicles, bookings, conversations..."
                  className="flex-1 bg-transparent text-sm text-gray-900 dark:text-white placeholder-gray-400 outline-none"
                />
                <button onClick={() => { setShowSearch(false); setSearchQuery(''); }}>
                  <X size={16} className="text-gray-400" />
                </button>
              </div>
              {!searchQuery && (
                <div className="p-4 space-y-1">
                  <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-2">Quick Navigate</p>
                  {[
                    { label: 'Fleet Overview', to: '/dashboard/operations', hint: 'Operations' },
                    { label: 'Escalations', to: '/dashboard/manager#escalations', hint: 'Manager' },
                    { label: 'Conversations', to: '/dashboard/conversations', hint: 'All Roles' },
                    { label: 'Recall Management', to: '/dashboard/recalls', hint: 'Operations' },
                    { label: 'Reports', to: '/dashboard/reports', hint: 'Manager/Executive' },
                  ].map((item) => (
                    <button
                      key={item.to}
                      onClick={() => { navigate(item.to); setShowSearch(false); setSearchQuery(''); }}
                      className="flex items-center justify-between w-full px-3 py-2 rounded-xl hover:bg-gray-50 dark:hover:bg-white/5 transition-colors"
                    >
                      <span className="text-sm text-gray-700 dark:text-gray-300">{item.label}</span>
                      <span className="text-[10px] text-gray-400 bg-gray-100 dark:bg-white/10 px-2 py-0.5 rounded-md">{item.hint}</span>
                    </button>
                  ))}
                </div>
              )}
              {searchQuery && (
                <div className="p-4">
                  <p className="text-xs text-gray-400 text-center py-4">
                    Searching for "<span className="text-[#6366f1]">{searchQuery}</span>"…
                  </p>
                </div>
              )}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
