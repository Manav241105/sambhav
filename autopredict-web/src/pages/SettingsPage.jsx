import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Settings2, Users, Bell, Brain, Clock,
    CheckCircle, ChevronRight, Save, AlertTriangle,
} from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';

const spring = { type: 'spring', stiffness: 100, damping: 10 };

const TABS = [
    { id: 'team', label: 'Team Management', icon: Users },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'ai', label: 'AI Agent Controls', icon: Brain },
    { id: 'bay', label: 'Bay & Hours', icon: Clock },
];

const PRIORITY_THRESHOLDS = [
    { key: 'p0_rul', label: 'P0 Alert — Trigger at RUL (days) ≤', defaultVal: 7, min: 1, max: 14 },
    { key: 'p1_rul', label: 'P1 Alert — Trigger at RUL (days) ≤', defaultVal: 14, min: 7, max: 30 },
    { key: 'auto_schedule', label: 'Auto-schedule when RUL ≤ (days)', defaultVal: 10, min: 3, max: 21 },
];

export default function SettingsPage() {
    const [activeTab, setActiveTab] = useState('team');
    const [saved, setSaved] = useState(false);

    // Team
    const [teamMembers] = useState([
        { id: 1, name: 'Sarah Mitchell', email: 'sarah@autopredict.io', role: 'Operations', status: 'Active' },
        { id: 2, name: 'James Park', email: 'james@autopredict.io', role: 'Manager', status: 'Active' },
        { id: 3, name: 'Priya Sharma', email: 'priya@autopredict.io', role: 'Executive', status: 'Active' },
        { id: 4, name: 'Tom Wallace', email: 'tom@autopredict.io', role: 'Operations', status: 'Pending' },
    ]);

    // Notifications
    const [notifPrefs, setNotifPrefs] = useState({
        email_p0: true,
        email_p1: true,
        email_p2: false,
        sms_p0: true,
        sms_p1: false,
        browser_all: true,
    });

    // AI Controls
    const [aiPrefs, setAiPrefs] = useState({
        p0_rul: 7,
        p1_rul: 14,
        auto_schedule: 10,
        agent_tone: 'Professional',
        escalation_on_no_response: true,
        follow_up_days: 3,
    });

    // Bay config
    const [bayPrefs, setBayPrefs] = useState({
        bays: 6,
        open_hour: 8,
        close_hour: 18,
        weekend_open: false,
    });

    const handleSave = () => {
        setSaved(true);
        setTimeout(() => setSaved(false), 2500);
    };

    const Toggle = ({ value, onChange }) => (
        <button
            onClick={() => onChange(!value)}
            className={`relative w-10 h-5 rounded-full transition-colors ${value ? 'bg-[#6366f1]' : 'bg-gray-200 dark:bg-white/10'}`}
        >
            <motion.div
                animate={{ x: value ? 22 : 2 }}
                transition={{ type: 'spring', stiffness: 300, damping: 25 }}
                className="absolute top-1 w-3 h-3 rounded-full bg-white shadow"
            />
        </button>
    );

    return (
        <DashboardLayout title="Settings">
            <div className="flex gap-6">
                {/* Tab list */}
                <div className="w-52 shrink-0 space-y-1">
                    {TABS.map((tab) => {
                        const Icon = tab.icon;
                        return (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`w-full flex items-center gap-3 px-4 py-3 rounded-2xl text-sm font-medium text-left transition-colors ${activeTab === tab.id
                                        ? 'bg-[#6366f1]/10 text-[#6366f1]'
                                        : 'text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-white/5'
                                    }`}
                            >
                                <Icon size={18} className="shrink-0" />
                                {tab.label}
                            </button>
                        );
                    })}
                </div>

                {/* Settings content */}
                <AnimatePresence mode="wait">
                    <motion.div
                        key={activeTab}
                        initial={{ opacity: 0, x: 16 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -16 }}
                        transition={spring}
                        className="flex-1 bg-white dark:bg-white/5 border border-gray-200 dark:border-gray-700 rounded-3xl p-6"
                    >
                        {activeTab === 'team' && (
                            <div>
                                <h3 className="text-sm font-extrabold text-gray-900 dark:text-white mb-5">Team Members</h3>
                                <div className="space-y-3">
                                    {teamMembers.map((m) => (
                                        <div key={m.id} className="flex items-center gap-4 p-4 border border-gray-100 dark:border-white/5 rounded-2xl">
                                            <div className="w-9 h-9 rounded-xl bg-[#6366f1]/15 text-[#6366f1] font-bold text-xs flex items-center justify-center">
                                                {m.name.slice(0, 2).toUpperCase()}
                                            </div>
                                            <div className="flex-1">
                                                <p className="text-sm font-bold text-gray-900 dark:text-white">{m.name}</p>
                                                <p className="text-xs text-gray-400">{m.email}</p>
                                            </div>
                                            <span className="text-[10px] bg-gray-100 dark:bg-white/10 text-gray-400 px-2 py-0.5 rounded-md">{m.role}</span>
                                            <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${m.status === 'Active' ? 'bg-emerald-500/15 text-emerald-500' : 'bg-amber-500/15 text-amber-500'}`}>
                                                {m.status}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                                <button className="mt-4 px-4 py-2 text-xs font-bold rounded-xl bg-[#6366f1]/10 text-[#6366f1] hover:bg-[#6366f1]/20 transition-colors">
                                    + Invite team member
                                </button>
                            </div>
                        )}

                        {activeTab === 'notifications' && (
                            <div>
                                <h3 className="text-sm font-extrabold text-gray-900 dark:text-white mb-5">Notification Preferences</h3>
                                <div className="space-y-6">
                                    {/* Email */}
                                    <div>
                                        <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Email Alerts</p>
                                        <div className="space-y-3">
                                            {[
                                                { key: 'email_p0', label: 'P0 Critical alerts via email' },
                                                { key: 'email_p1', label: 'P1 High priority alerts via email' },
                                                { key: 'email_p2', label: 'P2 Medium priority alerts via email' },
                                            ].map(({ key, label }) => (
                                                <div key={key} className="flex items-center justify-between py-2">
                                                    <span className="text-sm text-gray-700 dark:text-gray-300">{label}</span>
                                                    <Toggle value={notifPrefs[key]} onChange={(v) => setNotifPrefs((p) => ({ ...p, [key]: v }))} />
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                    {/* SMS */}
                                    <div>
                                        <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">SMS Alerts</p>
                                        <div className="space-y-3">
                                            {[
                                                { key: 'sms_p0', label: 'P0 Critical alerts via SMS' },
                                                { key: 'sms_p1', label: 'P1 High priority alerts via SMS' },
                                            ].map(({ key, label }) => (
                                                <div key={key} className="flex items-center justify-between py-2">
                                                    <span className="text-sm text-gray-700 dark:text-gray-300">{label}</span>
                                                    <Toggle value={notifPrefs[key]} onChange={(v) => setNotifPrefs((p) => ({ ...p, [key]: v }))} />
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                    {/* Browser */}
                                    <div>
                                        <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Browser</p>
                                        <div className="flex items-center justify-between py-2">
                                            <span className="text-sm text-gray-700 dark:text-gray-300">Show browser push notifications (all alerts)</span>
                                            <Toggle value={notifPrefs.browser_all} onChange={(v) => setNotifPrefs((p) => ({ ...p, browser_all: v }))} />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeTab === 'ai' && (
                            <div>
                                <h3 className="text-sm font-extrabold text-gray-900 dark:text-white mb-5">AI Agent Controls</h3>
                                <div className="space-y-5">
                                    {PRIORITY_THRESHOLDS.map(({ key, label, min, max }) => (
                                        <div key={key}>
                                            <div className="flex items-center justify-between mb-2">
                                                <label className="text-sm text-gray-700 dark:text-gray-300">{label}</label>
                                                <span className="text-sm font-bold text-[#6366f1]">{aiPrefs[key]} days</span>
                                            </div>
                                            <input
                                                type="range"
                                                min={min}
                                                max={max}
                                                value={aiPrefs[key]}
                                                onChange={(e) => setAiPrefs((p) => ({ ...p, [key]: Number(e.target.value) }))}
                                                className="w-full accent-[#6366f1]"
                                            />
                                            <div className="flex justify-between text-[10px] text-gray-400 mt-0.5">
                                                <span>{min}d</span><span>{max}d</span>
                                            </div>
                                        </div>
                                    ))}
                                    <div>
                                        <label className="text-sm text-gray-700 dark:text-gray-300 block mb-2">Agent communication tone</label>
                                        <div className="flex gap-2">
                                            {['Professional', 'Friendly', 'Urgent'].map((t) => (
                                                <button
                                                    key={t}
                                                    onClick={() => setAiPrefs((p) => ({ ...p, agent_tone: t }))}
                                                    className={`px-4 py-2 text-xs font-bold rounded-xl transition-colors ${aiPrefs.agent_tone === t ? 'bg-[#6366f1]/15 text-[#6366f1]' : 'bg-gray-100 dark:bg-white/5 text-gray-500 dark:text-gray-400'}`}
                                                >
                                                    {t}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <p className="text-sm text-gray-700 dark:text-gray-300">Auto-escalate if customer doesn't respond</p>
                                            <p className="text-xs text-gray-400">Assigns to human agent if no reply after set days</p>
                                        </div>
                                        <Toggle
                                            value={aiPrefs.escalation_on_no_response}
                                            onChange={(v) => setAiPrefs((p) => ({ ...p, escalation_on_no_response: v }))}
                                        />
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeTab === 'bay' && (
                            <div>
                                <h3 className="text-sm font-extrabold text-gray-900 dark:text-white mb-5">Bay Configuration</h3>
                                <div className="space-y-5">
                                    <div>
                                        <div className="flex items-center justify-between mb-2">
                                            <label className="text-sm text-gray-700 dark:text-gray-300">Number of active bays</label>
                                            <span className="text-sm font-bold text-[#6366f1]">{bayPrefs.bays} bays</span>
                                        </div>
                                        <input
                                            type="range" min={1} max={20} value={bayPrefs.bays}
                                            onChange={(e) => setBayPrefs((p) => ({ ...p, bays: Number(e.target.value) }))}
                                            className="w-full accent-[#6366f1]"
                                        />
                                        <div className="flex justify-between text-[10px] text-gray-400 mt-0.5"><span>1</span><span>20</span></div>
                                    </div>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="text-xs text-gray-400 block mb-2">Opening hour</label>
                                            <select
                                                value={bayPrefs.open_hour}
                                                onChange={(e) => setBayPrefs((p) => ({ ...p, open_hour: Number(e.target.value) }))}
                                                className="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-white/5 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-900 dark:text-white outline-none"
                                            >
                                                {[6, 7, 8, 9, 10].map((h) => <option key={h} value={h}>{h}:00</option>)}
                                            </select>
                                        </div>
                                        <div>
                                            <label className="text-xs text-gray-400 block mb-2">Closing hour</label>
                                            <select
                                                value={bayPrefs.close_hour}
                                                onChange={(e) => setBayPrefs((p) => ({ ...p, close_hour: Number(e.target.value) }))}
                                                className="w-full px-3 py-2 text-sm bg-gray-100 dark:bg-white/5 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-900 dark:text-white outline-none"
                                            >
                                                {[16, 17, 18, 19, 20, 21].map((h) => <option key={h} value={h}>{h}:00</option>)}
                                            </select>
                                        </div>
                                    </div>
                                    <div className="flex items-center justify-between">
                                        <p className="text-sm text-gray-700 dark:text-gray-300">Weekend service available</p>
                                        <Toggle value={bayPrefs.weekend_open} onChange={(v) => setBayPrefs((p) => ({ ...p, weekend_open: v }))} />
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Save button */}
                        <div className="mt-8 pt-5 border-t border-gray-100 dark:border-white/5 flex items-center gap-3">
                            <motion.button
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.97 }}
                                onClick={handleSave}
                                className={`flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-bold transition-colors ${saved ? 'bg-emerald-500/15 text-emerald-500' : 'bg-[#6366f1] text-gray-900 hover:bg-[#d4ff5c]'}`}
                            >
                                {saved ? <CheckCircle size={14} /> : <Save size={14} />}
                                {saved ? 'Saved!' : 'Save changes'}
                            </motion.button>
                            {saved && <span className="text-xs text-gray-400">Changes saved locally</span>}
                        </div>
                    </motion.div>
                </AnimatePresence>
            </div>
        </DashboardLayout>
    );
}
