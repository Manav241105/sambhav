import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useOutletContext } from 'react-router-dom';
import { Send } from 'lucide-react';

const spring = { type: 'spring', stiffness: 100, damping: 10 };

export default function OpsConversations() {
    const { conversations } = useOutletContext();
    const [selected, setSelected] = useState(null);
    const [inputMsg, setInputMsg] = useState('');

    // Group by vehicle
    const grouped = React.useMemo(() => {
        const map = {};
        conversations.forEach((t) => {
            if (!map[t.vehicle_id]) map[t.vehicle_id] = { vehicle_id: t.vehicle_id, customer_name: t.customer_name || 'Unknown', channel: t.channel, turns: [] };
            map[t.vehicle_id].turns.push(t);
        });
        return Object.values(map).sort((a, b) => b.turns.length - a.turns.length);
    }, [conversations]);

    const current = selected ? grouped.find((g) => g.vehicle_id === selected) : null;

    return (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={spring}>
            <h2 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-2">
                Live Conversation Feed
            </h2>
            <p className="text-sm text-gray-400 dark:text-gray-500 mb-6 max-w-2xl leading-relaxed">
                Live transcript of AI-to-Customer SMS/Chat engagements. Operators can shadow these conversations and intervene
                if the AI encounters an unmapped edge case or the customer escalates unexpectedly.
            </p>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[540px]">
                {/* Thread list */}
                <div className="border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl p-4 overflow-y-auto flex flex-col gap-2">
                    {grouped.length === 0 ? (
                        <p className="text-xs text-gray-400 text-center py-8">No conversations</p>
                    ) : (
                        grouped.map((g) => (
                            <button
                                key={g.vehicle_id}
                                onClick={() => setSelected(g.vehicle_id)}
                                className={`w-full text-left flex items-start gap-3 p-3 rounded-2xl border transition-colors ${selected === g.vehicle_id
                                        ? 'border-[#6366f1] bg-[#6366f1]/5'
                                        : 'border-gray-100 dark:border-white/5 hover:bg-gray-50 dark:hover:bg-white/[0.03]'
                                    }`}
                            >
                                <div className="w-8 h-8 rounded-xl bg-[#6366f1]/15 flex items-center justify-center shrink-0">
                                    <span className="text-xs font-bold text-[#6366f1]">{g.vehicle_id.slice(-2)}</span>
                                </div>
                                <div className="min-w-0">
                                    <p className="text-xs font-bold text-gray-900 dark:text-white truncate">{g.vehicle_id}</p>
                                    <p className="text-[10px] text-gray-400 truncate">{g.customer_name} · {g.channel}</p>
                                    <p className="text-[10px] text-gray-500 dark:text-gray-500 mt-0.5">{g.turns.length} messages</p>
                                </div>
                            </button>
                        ))
                    )}
                </div>

                {/* Chat window */}
                <div className="lg:col-span-2 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl flex flex-col overflow-hidden">
                    {!current ? (
                        <div className="flex-1 flex items-center justify-center">
                            <p className="text-sm text-gray-400">Select a conversation thread</p>
                        </div>
                    ) : (
                        <>
                            {/* Header */}
                            <div className="px-5 py-4 border-b border-gray-200 dark:border-gray-700">
                                <p className="text-sm font-bold text-gray-900 dark:text-white">{current.vehicle_id}</p>
                                <p className="text-xs text-gray-400">{current.customer_name} · {current.channel}</p>
                            </div>

                            {/* Messages */}
                            <div className="flex-1 overflow-y-auto p-4 space-y-3">
                                {[...current.turns]
                                    .sort((a, b) => a.turn_number - b.turn_number)
                                    .map((t, i) => (
                                        <div key={i} className={`flex gap-2 ${t.direction === 'INBOUND' ? 'flex-row-reverse' : ''}`}>
                                            <div className={`px-4 py-2.5 rounded-2xl text-xs max-w-[75%] leading-relaxed ${t.direction === 'OUTBOUND'
                                                    ? 'bg-[#6366f1]/10 text-gray-800 dark:text-gray-200 rounded-tl-sm'
                                                    : 'bg-gray-100 dark:bg-white/10 text-gray-700 dark:text-gray-300 rounded-tr-sm'
                                                }`}>
                                                <span className={`block text-[9px] font-bold mb-1 ${t.direction === 'OUTBOUND' ? 'text-[#6366f1]' : 'text-gray-400'}`}>
                                                    {t.direction === 'OUTBOUND' ? 'AI Agent' : 'Customer'}
                                                </span>
                                                {t.message}
                                            </div>
                                        </div>
                                    ))}
                            </div>

                            {/* Reply bar */}
                            <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 flex items-center gap-3">
                                <input
                                    value={inputMsg}
                                    onChange={(e) => setInputMsg(e.target.value)}
                                    placeholder="Override AI — type a manual response…"
                                    className="flex-1 bg-gray-100 dark:bg-white/5 rounded-xl px-4 py-2.5 text-xs text-gray-900 dark:text-white placeholder-gray-400 outline-none"
                                />
                                <button
                                    onClick={() => { if (inputMsg.trim()) setInputMsg(''); }}
                                    className="p-2.5 rounded-xl bg-[#6366f1] hover:bg-[#4f46e5] transition-colors"
                                >
                                    <Send size={14} className="text-gray-900" />
                                </button>
                            </div>
                        </>
                    )}
                </div>
            </div>
        </motion.div>
    );
}
