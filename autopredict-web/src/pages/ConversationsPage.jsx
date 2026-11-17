import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import {
    MessageSquare, Send, Search, Filter, ArrowUpRight, ArrowDownRight,
    Clock, ChevronRight, X, Bot, User, Wifi, RefreshCw, CheckCircle,
} from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';
import LiveEventBus from '../components/LiveEventBus';

const API = 'http://localhost:8001';
const spring = { type: 'spring', stiffness: 100, damping: 10 };

/* ── Group conversation turns by vehicle ─────────── */
function groupByVehicle(turns) {
    const map = {};
    turns.forEach((t) => {
        const key = t.vehicle_id;
        if (!map[key]) {
            map[key] = {
                vehicle_id: key,
                customer_name: t.customer_name || 'Unknown',
                channel: t.channel,
                status: t.status,
                turns: [],
                lastMessage: null,
            };
        }
        map[key].turns.push(t);
        map[key].lastMessage = t;
        if (t.status === 'OPEN') map[key].status = 'OPEN';
    });
    return Object.values(map).sort((a, b) => {
        if (a.status === 'OPEN' && b.status !== 'OPEN') return -1;
        if (b.status === 'OPEN' && a.status !== 'OPEN') return 1;
        return (b.turns.length) - (a.turns.length);
    });
}

const tooltipStyle = {
    backgroundColor: '#1f2937',
    border: '1px solid #374151',
    borderRadius: '12px',
    fontSize: 12,
    color: '#fff',
};

export default function ConversationsPage() {
    const [conversations, setConversations] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedThread, setSelectedThread] = useState(null);
    const [reply, setReply] = useState('');
    const [searchQ, setSearchQ] = useState('');
    const [filterStatus, setFilterStatus] = useState('ALL');
    const [sending, setSending] = useState(false);

    const fetchAll = useCallback(async () => {
        try {
            const r = await axios.get(`${API}/api/conversations`);
            const turns = Array.isArray(r.data) ? r.data : [];
            setConversations(groupByVehicle(turns));
        } catch (err) {
            console.error('Conversations fetch error:', err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchAll();
        const i = setInterval(fetchAll, 30_000);
        return () => clearInterval(i);
    }, [fetchAll]);

    const filtered = conversations.filter((c) => {
        const matchSearch = !searchQ ||
            c.vehicle_id.toLowerCase().includes(searchQ.toLowerCase()) ||
            c.customer_name.toLowerCase().includes(searchQ.toLowerCase());
        const matchStatus = filterStatus === 'ALL' || c.status === filterStatus;
        return matchSearch && matchStatus;
    });

    const handleSendReply = async (e) => {
        e.preventDefault();
        if (!reply.trim() || !selectedThread) return;
        setSending(true);
        // Optimistically add to UI
        const newTurn = {
            vehicle_id: selectedThread.vehicle_id,
            customer_name: selectedThread.customer_name,
            direction: 'OUTBOUND',
            channel: selectedThread.channel,
            message: reply.trim(),
            turn_number: selectedThread.turns.length + 1,
            status: 'OPEN',
        };
        setSelectedThread((prev) => ({ ...prev, turns: [...prev.turns, newTurn] }));
        setReply('');
        setSending(false);
    };

    return (
        <DashboardLayout title="AI Conversations">
            <LiveEventBus onConversationTurn={fetchAll} onAnyEvent={fetchAll} />

            <div className="flex gap-6 h-[calc(100vh-160px)]">
                {/* ── Thread List ─────────────────────────── */}
                <div className="w-80 shrink-0 flex flex-col border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl overflow-hidden">
                    {/* Search & filter */}
                    <div className="p-4 border-b border-gray-200 dark:border-gray-700 space-y-3">
                        <div className="flex items-center gap-2 px-3 py-2 bg-gray-100 dark:bg-white/5 rounded-xl">
                            <Search size={14} className="text-gray-400 shrink-0" />
                            <input
                                value={searchQ}
                                onChange={(e) => setSearchQ(e.target.value)}
                                placeholder="Search vehicle or customer..."
                                className="flex-1 bg-transparent text-sm text-gray-900 dark:text-white placeholder-gray-400 outline-none"
                            />
                        </div>
                        <div className="flex gap-2">
                            {['ALL', 'OPEN', 'CLOSED'].map((s) => (
                                <button
                                    key={s}
                                    onClick={() => setFilterStatus(s)}
                                    className={`flex-1 py-1.5 text-[10px] font-bold rounded-lg transition-colors ${filterStatus === s
                                            ? 'bg-[#6366f1]/15 text-[#6366f1]'
                                            : 'bg-gray-100 dark:bg-white/5 text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-white/10'
                                        }`}
                                >
                                    {s}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Thread items */}
                    <div className="flex-1 overflow-y-auto divide-y divide-gray-100 dark:divide-white/5">
                        {loading ? (
                            [...Array(5)].map((_, i) => (
                                <div key={i} className="p-4 animate-pulse flex gap-3">
                                    <div className="w-10 h-10 rounded-full bg-gray-200 dark:bg-white/10 shrink-0" />
                                    <div className="flex-1 space-y-2">
                                        <div className="h-3 bg-gray-200 dark:bg-white/10 rounded w-24" />
                                        <div className="h-2 bg-gray-200 dark:bg-white/10 rounded w-40" />
                                    </div>
                                </div>
                            ))
                        ) : filtered.length === 0 ? (
                            <div className="p-8 text-center text-xs text-gray-400">No conversations found</div>
                        ) : (
                            filtered.map((thread) => (
                                <motion.button
                                    key={thread.vehicle_id}
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    onClick={() => setSelectedThread(thread)}
                                    className={`w-full text-left p-4 flex items-start gap-3 hover:bg-gray-50 dark:hover:bg-white/[0.02] transition-colors ${selectedThread?.vehicle_id === thread.vehicle_id ? 'bg-[#6366f1]/5 border-l-2 border-[#6366f1]' : ''
                                        }`}
                                >
                                    <div className="w-10 h-10 rounded-full bg-[#6366f1]/15 flex items-center justify-center text-[#6366f1] font-bold text-xs shrink-0">
                                        {thread.vehicle_id.slice(-3)}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center justify-between mb-0.5">
                                            <span className="text-xs font-bold text-gray-900 dark:text-white">{thread.vehicle_id}</span>
                                            <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full ${thread.status === 'OPEN' ? 'bg-[#6366f1]/15 text-[#6366f1]' : 'bg-gray-100 dark:bg-white/10 text-gray-400'}`}>
                                                {thread.status}
                                            </span>
                                        </div>
                                        <p className="text-[11px] text-gray-500 dark:text-gray-400 truncate">{thread.customer_name}</p>
                                        <p className="text-[10px] text-gray-400 dark:text-gray-500 truncate mt-0.5">
                                            {thread.lastMessage?.message?.slice(0, 55)}...
                                        </p>
                                        <div className="flex items-center gap-2 mt-1">
                                            <span className="text-[9px] bg-gray-100 dark:bg-white/10 text-gray-400 px-1.5 py-0.5 rounded">{thread.channel}</span>
                                            <span className="text-[9px] text-gray-400">{thread.turns.length} turns</span>
                                        </div>
                                    </div>
                                </motion.button>
                            ))
                        )}
                    </div>
                </div>

                {/* ── Chat Window ─────────────────────────── */}
                <div className="flex-1 flex flex-col border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl overflow-hidden">
                    {selectedThread ? (
                        <>
                            {/* Chat header */}
                            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-white/[0.02]">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-full bg-[#6366f1]/15 flex items-center justify-center text-[#6366f1] font-bold text-xs">
                                        {selectedThread.vehicle_id.slice(-3)}
                                    </div>
                                    <div>
                                        <p className="text-sm font-extrabold text-gray-900 dark:text-white">{selectedThread.vehicle_id}</p>
                                        <p className="text-xs text-gray-400">{selectedThread.customer_name} · {selectedThread.channel}</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3">
                                    <span className={`text-[10px] font-bold px-2 py-1 rounded-full ${selectedThread.status === 'OPEN' ? 'bg-[#6366f1]/15 text-[#6366f1]' : 'bg-gray-100 dark:bg-white/10 text-gray-400'}`}>
                                        {selectedThread.status}
                                    </span>
                                    <button onClick={() => setSelectedThread(null)} className="p-2 rounded-xl hover:bg-gray-100 dark:hover:bg-white/5">
                                        <X size={14} className="text-gray-400" />
                                    </button>
                                </div>
                            </div>

                            {/* Messages */}
                            <div className="flex-1 overflow-y-auto p-6 space-y-4">
                                {[...selectedThread.turns]
                                    .sort((a, b) => a.turn_number - b.turn_number)
                                    .map((turn, i) => {
                                        const isOutbound = turn.direction === 'OUTBOUND';
                                        return (
                                            <motion.div
                                                key={i}
                                                initial={{ opacity: 0, y: 10 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                transition={{ ...spring, delay: i * 0.04 }}
                                                className={`flex gap-3 ${isOutbound ? '' : 'flex-row-reverse'}`}
                                            >
                                                <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-1 ${isOutbound ? 'bg-[#6366f1]/15 text-[#6366f1]' : 'bg-blue-500/15 text-blue-400'}`}>
                                                    {isOutbound ? <Bot size={14} /> : <User size={14} />}
                                                </div>
                                                <div className={`max-w-[70%] ${isOutbound ? '' : ''}`}>
                                                    <p className={`text-[10px] font-bold mb-1 ${isOutbound ? 'text-[#6366f1]' : 'text-blue-400 text-right'}`}>
                                                        {isOutbound ? 'AI Agent' : turn.customer_name}
                                                    </p>
                                                    <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${isOutbound
                                                            ? 'bg-gray-50 dark:bg-white/[0.04] text-gray-700 dark:text-gray-300 rounded-tl-none border border-gray-100 dark:border-white/5'
                                                            : 'bg-blue-50 dark:bg-blue-500/10 text-gray-700 dark:text-gray-300 rounded-tr-none border border-blue-100 dark:border-blue-500/10'
                                                        }`}>
                                                        {turn.message}
                                                    </div>
                                                </div>
                                            </motion.div>
                                        );
                                    })}
                            </div>

                            {/* Reply input */}
                            <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700">
                                <div className="flex items-center gap-2 mb-2">
                                    <Bot size={12} className="text-[#6366f1]" />
                                    <span className="text-[10px] text-gray-400">Send as AI Agent — override / inject a message</span>
                                </div>
                                <form onSubmit={handleSendReply} className="flex items-center gap-3">
                                    <input
                                        value={reply}
                                        onChange={(e) => setReply(e.target.value)}
                                        placeholder="Type an override message... (will be sent as OUTBOUND)"
                                        className="flex-1 px-4 py-2.5 text-sm bg-gray-100 dark:bg-white/5 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-900 dark:text-white placeholder-gray-400 outline-none focus:ring-2 focus:ring-[#6366f1]/50"
                                    />
                                    <motion.button
                                        type="submit"
                                        disabled={!reply.trim() || sending}
                                        whileHover={{ scale: 1.05 }}
                                        whileTap={{ scale: 0.95 }}
                                        className="p-3 rounded-xl bg-[#6366f1] text-gray-900 disabled:opacity-40 disabled:cursor-not-allowed"
                                    >
                                        <Send size={16} />
                                    </motion.button>
                                </form>
                            </div>
                        </>
                    ) : (
                        <div className="flex-1 flex flex-col items-center justify-center gap-4 text-center">
                            <div className="w-20 h-20 rounded-3xl bg-[#6366f1]/10 flex items-center justify-center">
                                <MessageSquare size={36} className="text-[#6366f1]" />
                            </div>
                            <div>
                                <p className="text-sm font-bold text-gray-900 dark:text-white">Select a conversation</p>
                                <p className="text-xs text-gray-400 mt-1">Pick a thread from the left to view the full chat history</p>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </DashboardLayout>
    );
}
