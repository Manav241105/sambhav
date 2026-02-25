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
} from 'lucide-react';
import ThemeToggle from './ThemeToggle';

/* ── Spring matching HeroSection ─────────────────── */
const spring = { type: 'spring', stiffness: 100, damping: 10 };

/* Navigation links per role */
const NAV_ITEMS = {
  ops: [
    { to: '/dashboard/operations', icon: LayoutDashboard, label: 'Overview' },
    { to: '/dashboard/operations#fleet', icon: Truck,            label: 'Fleet' },
    { to: '/dashboard/operations#calendar', icon: CalendarDays,  label: 'Bay Calendar' },
    { to: '/dashboard/operations#conversations', icon: MessageSquare, label: 'Conversations' },
  ],
  manager: [
    { to: '/dashboard/manager', icon: LayoutDashboard, label: 'Overview' },
    { to: '/dashboard/manager#escalations', icon: ShieldCheck, label: 'Escalations' },
    { to: '/dashboard/manager#revenue', icon: BarChart3,       label: 'Revenue' },
    { to: '/dashboard/manager#workload', icon: Settings2,      label: 'Workload' },
  ],
  executive: [
    { to: '/dashboard/executive', icon: LayoutDashboard, label: 'Overview' },
    { to: '/dashboard/executive#fleet-health', icon: Truck,    label: 'Fleet Health' },
    { to: '/dashboard/executive#trends', icon: BarChart3,      label: 'Trends' },
    { to: '/dashboard/executive#recalls', icon: ShieldCheck,   label: 'Recalls' },
  ],
};

const ROLE_LABELS = { ops: 'Operations', manager: 'Manager', executive: 'Executive' };

export default function Sidebar() {
  const navigate = useNavigate();
  const role = localStorage.getItem('ap_role') || 'ops';
  const items = NAV_ITEMS[role] || NAV_ITEMS.ops;
  const [collapsed, setCollapsed] = useState(false);

  const handleLogout = () => {
    localStorage.removeItem('ap_token');
    localStorage.removeItem('ap_role');
    navigate('/login');
  };

  return (
    <motion.aside
      animate={{ width: collapsed ? 72 : 256 }}
      transition={spring}
      className="fixed top-0 left-0 z-40 flex flex-col h-screen border-r bg-white dark:bg-[#0b0f19] border-gray-200 dark:border-gray-800"
    >
      {/* Logo row */}
      <div className="flex items-center justify-between px-4 h-16 border-b border-gray-200 dark:border-gray-800">
        <AnimatePresence mode="wait">
          {!collapsed && (
            <motion.span
              key="logo"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="text-lg font-extrabold text-gray-900 dark:text-white whitespace-nowrap"
            >
              Auto<span className="text-[#caff42]">Predict</span>
            </motion.span>
          )}
        </AnimatePresence>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1.5 rounded-lg text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-white/5 transition-colors"
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
            className="px-4 py-3"
          >
            <span className="inline-block px-2.5 py-1 text-[10px] font-bold tracking-wider uppercase rounded-full bg-[#caff42]/15 text-[#caff42]">
              {ROLE_LABELS[role]}
            </span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Nav links */}
      <nav className="flex-1 px-3 py-2 space-y-1 overflow-y-auto">
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `group flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-[#caff42]/10 text-[#caff42]'
                    : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-white/5'
                }`
              }
            >
              <Icon size={20} />
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
      <div className="px-3 py-3 space-y-1 border-t border-gray-200 dark:border-gray-800">
        <div className={`flex items-center ${collapsed ? 'justify-center' : 'px-3'}`}>
          <ThemeToggle />
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center w-full gap-3 px-3 py-2.5 text-sm font-medium text-gray-500 transition-colors rounded-xl hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/5"
        >
          <LogOut size={20} />
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
  );
}
