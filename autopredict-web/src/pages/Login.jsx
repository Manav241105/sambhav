import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ShieldCheck, BarChart3, Settings2, ArrowLeft } from 'lucide-react';

/* ── Spring config matching HeroSection ───────────── */
const spring = { type: 'spring', stiffness: 100, damping: 10 };

const ROLES = [
  {
    key: 'ops',
    label: 'Operations',
    desc: 'Fleet monitoring, scheduling & live conversations',
    icon: Settings2,
    path: '/dashboard/operations',
  },
  {
    key: 'manager',
    label: 'Manager',
    desc: 'SLAs, revenue pipeline & escalation queue',
    icon: BarChart3,
    path: '/dashboard/manager',
  },
  {
    key: 'executive',
    label: 'Executive',
    desc: 'KPI overview, trends & cost avoidance',
    icon: ShieldCheck,
    path: '/dashboard/executive',
  },
];

export default function Login() {
  const navigate = useNavigate();
  const [selected, setSelected] = useState(null);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLogin = (e) => {
    e.preventDefault();
    if (!selected) {
      setError('Please select a role first.');
      return;
    }
    if (!email || !password) {
      setError('Enter email and password.');
      return;
    }

    /* Mock JWT — store role + token in localStorage */
    const mockToken = btoa(JSON.stringify({ role: selected.key, email, exp: Date.now() + 86400000 }));
    localStorage.setItem('ap_token', mockToken);
    localStorage.setItem('ap_role', selected.key);

    navigate(selected.path);
  };

  return (
    <div className="relative flex items-center justify-center min-h-screen bg-[#f4f5f0] dark:bg-[#0b0f19] transition-colors overflow-hidden">
      {/* Subtle glow */}
      <div className="absolute w-[500px] h-[500px] rounded-full bg-[#6366f1] opacity-10 blur-[160px] -top-40 -left-40 pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={spring}
        className="relative z-10 w-full max-w-md px-8 py-10 mx-4 border bg-white/80 dark:bg-white/5 backdrop-blur-xl border-gray-200 dark:border-gray-700 rounded-3xl"
      >
        {/* Back link */}
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-1 mb-6 text-sm font-medium text-gray-400 transition-colors hover:text-gray-900 dark:hover:text-white"
        >
          <ArrowLeft size={16} /> Back to Home
        </button>

        <h1 className="text-2xl font-extrabold text-gray-900 dark:text-white">
          Sign in to <span className="text-[#6366f1]">AutoPredict</span>
        </h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Select your role, then log in to access your dashboard.
        </p>

        {/* Role selector */}
        <div className="grid grid-cols-3 gap-3 mt-6">
          {ROLES.map((role) => {
            const Icon = role.icon;
            const active = selected?.key === role.key;
            return (
              <motion.button
                key={role.key}
                whileHover={{ scale: 1.04 }}
                whileTap={{ scale: 0.97 }}
                transition={spring}
                onClick={() => { setSelected(role); setError(''); }}
                className={`flex flex-col items-center gap-2 p-4 border rounded-2xl transition-colors cursor-pointer ${
                  active
                    ? 'border-[#6366f1] bg-[#6366f1]/10 dark:bg-[#6366f1]/5'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-500'
                }`}
              >
                <Icon size={22} className={active ? 'text-[#6366f1]' : 'text-gray-400'} />
                <span className={`text-xs font-semibold ${active ? 'text-[#6366f1]' : 'text-gray-600 dark:text-gray-300'}`}>
                  {role.label}
                </span>
              </motion.button>
            );
          })}
        </div>
        {selected && (
          <motion.p
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-2 text-xs text-center text-gray-400 dark:text-gray-500"
          >
            {selected.desc}
          </motion.p>
        )}

        {/* Login form */}
        <form onSubmit={handleLogin} className="mt-6 space-y-4">
          <div>
            <label className="block mb-1 text-xs font-medium text-gray-500 dark:text-gray-400">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@autopredict.io"
              className="w-full px-4 py-2.5 text-sm bg-gray-100 dark:bg-white/5 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#6366f1]/50 transition"
            />
          </div>
          <div>
            <label className="block mb-1 text-xs font-medium text-gray-500 dark:text-gray-400">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-4 py-2.5 text-sm bg-gray-100 dark:bg-white/5 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#6366f1]/50 transition"
            />
          </div>

          {error && (
            <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-xs font-medium text-red-500">
              {error}
            </motion.p>
          )}

          <motion.button
            type="submit"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.97 }}
            transition={spring}
            className="w-full py-3 text-sm font-bold text-[#0b0f19] transition-colors bg-[#6366f1] rounded-xl hover:brightness-110"
          >
            Sign In
          </motion.button>
        </form>

        <p className="mt-5 text-xs text-center text-gray-400 dark:text-gray-500">
          Mock auth — any email/password will work.
        </p>
      </motion.div>
    </div>
  );
}
