import React, { useState, useRef, useEffect } from 'react';
import { Send, FileText, ShieldAlert, CheckCircle, ChevronDown, ChevronUp, MessageSquare, Download, Bell, RefreshCw, AlertTriangle, Check, X, ClipboardList } from 'lucide-react';

const StarterQuestions = [
    "Show me high-risk invoices in BU-01",
    "Summarize vendor risk for VEND-999",
    "Any treasury variance this month?",
    "Draft a report for the audit committee on vendor VEND-999"
];

const ChatInterface = () => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    
    // Briefing state
    const [briefing, setBriefing] = useState(null);
    const [briefingOpen, setBriefingOpen] = useState(false);
    const [unreadBriefing, setUnreadBriefing] = useState(false);
    const [refreshing, setRefreshing] = useState(false);
    
    // Actions state
    const [pendingActions, setPendingActions] = useState([]);
    const [actionsOpen, setActionsOpen] = useState(false);

    const messagesEndRef = useRef(null);
    const conversationId = useRef(`conv-${Math.random().toString(36).substr(2, 9)}`);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(scrollToBottom, [messages]);

    useEffect(() => {
        // Fetch latest briefing on load
        const fetchBriefing = async () => {
            try {
                const res = await fetch('http://localhost:8000/api/briefings/latest');
                const data = await res.json();
                if (data && data.scan_timestamp) {
                    setBriefing(data);
                    setUnreadBriefing(true);
                }
            } catch (err) {
                console.error("Failed to load briefing", err);
            }
        };
        fetchBriefing();
        fetchPendingActions();
    }, []);

    const fetchPendingActions = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/actions/pending');
            const data = await res.json();
            setPendingActions(data);
        } catch (err) {
            console.error("Failed to load pending actions", err);
        }
    };

    const triggerBriefingRefresh = async () => {
        setRefreshing(true);
        try {
            const res = await fetch('http://localhost:8000/api/briefings/trigger', { method: 'POST' });
            const data = await res.json();
            if (data.status === 'success') {
                setBriefing(data.briefing);
                setUnreadBriefing(true);
                if (!briefingOpen) setBriefingOpen(true);
            }
        } catch (err) {
            console.error("Failed to refresh briefing", err);
        } finally {
            setRefreshing(false);
        }
    };

    const handleSend = async (text) => {
        if (!text.trim()) return;
        
        const userMsg = { role: 'user', content: text };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setLoading(true);

        try {
            const response = await fetch('http://localhost:8000/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: text,
                    conversation_id: conversationId.current
                })
            });
            const data = await response.json();
            
            const botMsg = { 
                role: 'assistant', 
                content: data.answer,
                sources: data.sources,
                low_confidence: data.low_confidence,
                actions: data.actions || [],
                specialists_used: data.specialists_used || []
            };
            setMessages(prev => [...prev, botMsg]);
        } catch (error) {
            console.error("Error sending message:", error);
            setMessages(prev => [...prev, { role: 'assistant', content: 'Error communicating with server.' }]);
        } finally {
            setLoading(false);
            fetchPendingActions(); // refresh global queue
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend(input);
        }
    };

    return (
        <div className="flex h-screen bg-slate-900 text-slate-200 font-sans">
            {/* Sidebar */}
            <div className="w-64 bg-slate-900/95 border-r border-slate-800 flex flex-col z-20 shadow-xl">
                <div className="p-6 border-b border-slate-800 flex items-center gap-3">
                    <div className="bg-indigo-500/20 p-2 rounded-lg border border-indigo-500/30">
                        <ShieldAlert className="w-5 h-5 text-indigo-400" />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold tracking-tight text-white">FinSage</h1>
                        <p className="text-[10px] font-medium text-slate-400 uppercase tracking-wider mt-0.5">Enterprise Copilot</p>
                    </div>
                </div>

                {/* Briefing Notification in Sidebar */}
                <div className="p-4 border-b border-slate-800">
                    <button 
                        onClick={() => {
                            setBriefingOpen(!briefingOpen);
                            setUnreadBriefing(false);
                        }}
                        className={`w-full flex items-center justify-between p-3 rounded-lg border transition-all ${briefingOpen ? 'bg-slate-800 border-indigo-500/50 shadow-sm' : 'bg-slate-800/50 border-slate-700 hover:bg-slate-800 hover:border-slate-600'}`}
                    >
                        <div className="flex items-center gap-2.5">
                            <div className="relative">
                                <Bell className={`w-4 h-4 ${briefingOpen ? 'text-indigo-400' : 'text-slate-400'}`} />
                                {unreadBriefing && !briefingOpen && (
                                    <span className="absolute -top-1 -right-1 w-2 h-2 bg-rose-500 rounded-full animate-pulse"></span>
                                )}
                            </div>
                            <span className="text-xs font-semibold text-slate-300">Morning Briefing</span>
                        </div>
                        {briefingOpen ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
                    </button>
                </div>

                {/* Pending Actions Sidebar Panel */}
                <div className="p-4 border-b border-slate-800">
                    <button 
                        onClick={() => {
                            setActionsOpen(!actionsOpen);
                        }}
                        className={`w-full flex items-center justify-between p-3 rounded-lg border transition-all ${actionsOpen ? 'bg-slate-800 border-amber-500/50 shadow-sm' : 'bg-slate-800/50 border-slate-700 hover:bg-slate-800 hover:border-slate-600'}`}
                    >
                        <div className="flex items-center gap-2.5">
                            <ClipboardList className={`w-4 h-4 ${actionsOpen ? 'text-amber-400' : 'text-slate-400'}`} />
                            <span className="text-xs font-semibold text-slate-300">Pending Actions</span>
                            {pendingActions.length > 0 && (
                                <span className="ml-2 px-1.5 py-0.5 bg-amber-500 text-white rounded text-[10px] font-bold">
                                    {pendingActions.length}
                                </span>
                            )}
                        </div>
                        {actionsOpen ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto p-4">
                    <h2 className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-3">Current Session</h2>
                    <div className="flex items-center gap-2 text-sm text-slate-300 bg-slate-800/80 border border-slate-700 p-2.5 rounded-lg shadow-sm">
                        <MessageSquare className="w-4 h-4 text-indigo-400" />
                        <span className="font-medium text-xs">Active Conversation</span>
                    </div>
                </div>
            </div>

            {/* Main Chat Area */}
            <div className="flex-1 flex flex-col relative bg-slate-900">
                {/* Global Pending Actions List (if toggled from sidebar) */}
                {actionsOpen && (
                    <div className="absolute left-0 top-0 bottom-0 w-80 bg-slate-800 border-r border-slate-700 shadow-2xl z-30 flex flex-col animate-in slide-in-from-left-8 duration-300">
                        <div className="p-4 border-b border-slate-700/50 bg-slate-800/50 flex justify-between items-center">
                            <div className="flex items-center gap-2">
                                <ClipboardList className="w-4 h-4 text-amber-400" />
                                <h2 className="text-sm font-semibold text-white tracking-wide">Action Queue</h2>
                            </div>
                            <button onClick={() => setActionsOpen(false)}><X className="w-4 h-4 text-slate-400 hover:text-white" /></button>
                        </div>
                        <div className="flex-1 overflow-y-auto p-4 space-y-3">
                            {pendingActions.length === 0 ? (
                                <p className="text-xs text-slate-400 italic text-center mt-4">No pending actions.</p>
                            ) : (
                                pendingActions.map((pa) => (
                                    <div key={pa.proposal_id} className="bg-slate-900/50 border border-amber-500/30 p-3 rounded-lg flex flex-col gap-2 shadow-sm">
                                        <div className="flex justify-between items-start">
                                            <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider">{pa.action_type.replace(/_/g, ' ')}</span>
                                            <span className="text-[9px] text-slate-500">{pa.proposal_id}</span>
                                        </div>
                                        <p className="text-xs text-slate-300 font-medium">{pa.target_entity_id}</p>
                                        <p className="text-[11px] text-slate-400">{pa.description}</p>
                                        <div className="flex justify-end gap-2 mt-1">
                                            <button 
                                                onClick={async () => {
                                                    await fetch(`http://localhost:8000/api/actions/${pa.proposal_id}/approve`, {method: 'POST'});
                                                    fetchPendingActions();
                                                }}
                                                className="text-[10px] px-2 py-1 bg-amber-500/20 text-amber-400 rounded hover:bg-amber-500/30 font-semibold"
                                            >
                                                Approve
                                            </button>
                                            <button 
                                                onClick={async () => {
                                                    await fetch(`http://localhost:8000/api/actions/${pa.proposal_id}/reject`, {method: 'POST'});
                                                    fetchPendingActions();
                                                }}
                                                className="text-[10px] px-2 py-1 bg-slate-700 text-slate-300 rounded hover:bg-slate-600 font-semibold"
                                            >
                                                Reject
                                            </button>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                )}
                <div className="flex-1 overflow-y-auto p-8 relative">
                    
                    {/* Morning Briefing Panel */}
                    {briefingOpen && briefing && (
                        <div className="max-w-3xl mx-auto mb-8 bg-slate-800/90 border border-indigo-500/30 rounded-2xl shadow-xl overflow-hidden animate-in fade-in slide-in-from-top-4 duration-300">
                            <div className="px-6 py-4 border-b border-slate-700/50 bg-slate-800/50 flex justify-between items-center">
                                <div className="flex items-center gap-2">
                                    <Bell className="w-5 h-5 text-indigo-400" />
                                    <h2 className="font-semibold text-white tracking-wide">Proactive Risk Briefing</h2>
                                </div>
                                <div className="flex items-center gap-4 text-xs font-medium text-slate-400">
                                    <span>Last Scan: {new Date(briefing.scan_timestamp).toLocaleTimeString()}</span>
                                    <button 
                                        onClick={triggerBriefingRefresh}
                                        disabled={refreshing}
                                        className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-700/50 hover:bg-slate-700 rounded-md text-slate-300 transition-colors disabled:opacity-50"
                                    >
                                        <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-indigo-400' : ''}`} />
                                        Refresh Now
                                    </button>
                                </div>
                            </div>
                            
                            <div className="p-6 space-y-6">
                                <p className="text-sm text-slate-300 leading-relaxed bg-slate-900/40 p-4 rounded-xl border border-slate-700/50">
                                    {briefing.summary_text}
                                </p>
                                
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {/* Compound Alerts */}
                                    <div className="bg-rose-500/5 border border-rose-500/20 rounded-xl p-4 flex flex-col">
                                        <div className="flex items-center gap-2 mb-3">
                                            <AlertTriangle className="w-4 h-4 text-rose-500" />
                                            <h3 className="text-xs font-bold text-rose-400 uppercase tracking-wider">Active Compound Alerts</h3>
                                            {briefing.compound_risk_alerts?.length > 0 && (
                                                <span className="ml-2 px-1.5 py-0.5 bg-rose-500 text-white rounded text-[10px] font-bold uppercase animate-pulse">
                                                    {briefing.compound_risk_alerts.length} New
                                                </span>
                                            )}
                                            <span className="ml-auto px-2 py-0.5 bg-rose-500/20 text-rose-400 rounded-full text-xs font-bold">{briefing.active_compound_alerts?.length || 0}</span>
                                        </div>
                                        <ul className="space-y-2 text-xs text-rose-300/80 flex-1 overflow-y-auto pr-2 max-h-40">
                                            {briefing.active_compound_alerts?.map((a, i) => (
                                                <li key={i} className="flex gap-2"><span className="text-rose-500 shrink-0">•</span> <span><strong className="text-rose-300">{a.business_unit_id}:</strong> {a.message}</span></li>
                                            ))}
                                            {(!briefing.active_compound_alerts || briefing.active_compound_alerts.length === 0) && <li className="italic text-rose-400/50">No multi-domain alerts detected.</li>}
                                        </ul>
                                    </div>
                                    
                                    {/* Active Findings */}
                                    <div className="bg-slate-900/30 border border-slate-700/50 rounded-xl p-4 flex flex-col">
                                        <div className="flex items-center gap-2 mb-3">
                                            <CheckCircle className="w-4 h-4 text-emerald-400" />
                                            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">Active Findings</h3>
                                            {briefing.new_findings?.length > 0 && (
                                                <span className="ml-2 px-1.5 py-0.5 bg-indigo-500 text-white rounded text-[10px] font-bold uppercase">
                                                    {briefing.new_findings.length} New
                                                </span>
                                            )}
                                            <span className="ml-auto px-2 py-0.5 bg-slate-700 text-slate-300 rounded-full text-xs font-bold">{briefing.active_findings?.length || 0}</span>
                                        </div>
                                        <ul className="space-y-2 text-xs text-slate-400 flex-1 overflow-y-auto pr-2 max-h-40">
                                            {briefing.active_findings?.map((f, i) => (
                                                <li key={i} className="flex gap-2"><span className="text-emerald-500 shrink-0">•</span> <span>{f}</span></li>
                                            ))}
                                            {(!briefing.active_findings || briefing.active_findings.length === 0) && <li className="italic text-slate-500">No anomalies surfaced.</li>}
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {messages.length === 0 ? (
                        <div className={`flex flex-col items-center justify-center max-w-2xl mx-auto text-center space-y-6 ${briefingOpen ? 'mt-12' : 'h-full'}`}>
                            <div className="w-16 h-16 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-2xl flex items-center justify-center mb-4 shadow-lg shadow-indigo-500/5">
                                <ShieldAlert className="w-8 h-8" />
                            </div>
                            <h2 className="text-2xl font-bold text-white tracking-wide">How can I assist your financial operations?</h2>
                            <p className="text-slate-400">I have direct agentic access to AP Invoices, Audit GL Exceptions, and Treasury Cashflow data.</p>
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full mt-8">
                                {StarterQuestions.map((q, idx) => (
                                    <button 
                                        key={idx} 
                                        onClick={() => handleSend(q)}
                                        className="text-left px-5 py-4 bg-slate-800/50 border border-slate-700 rounded-xl hover:bg-slate-800 hover:border-indigo-500/50 hover:shadow-lg transition-all text-sm text-slate-300 shadow-sm"
                                    >
                                        {q}
                                    </button>
                                ))}
                            </div>
                        </div>
                    ) : (
                        <div className="max-w-3xl mx-auto space-y-6">
                            {messages.map((msg, idx) => (
                                <MessageBubble key={idx} msg={msg} fetchPendingActions={fetchPendingActions} />
                            ))}
                            {loading && (
                                <div className="flex gap-4 p-5 bg-slate-800/80 rounded-2xl border border-slate-700 shadow-sm animate-pulse w-3/4 rounded-tl-none">
                                    <div className="w-8 h-8 bg-slate-700 rounded-lg"></div>
                                    <div className="flex-1 space-y-3 py-1">
                                        <div className="h-2 bg-slate-700 rounded w-3/4"></div>
                                        <div className="h-2 bg-slate-700 rounded w-1/2"></div>
                                    </div>
                                </div>
                            )}
                            <div ref={messagesEndRef} />
                        </div>
                    )}
                </div>

                {/* Input Area */}
                <div className="p-6 bg-slate-900/95 backdrop-blur border-t border-slate-800 z-10 shadow-[0_-10px_40px_rgba(0,0,0,0.2)]">
                    <div className="max-w-3xl mx-auto relative flex items-end gap-2">
                        <textarea
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Ask about vendors, invoices, or treasury variances..."
                            className="w-full resize-none rounded-xl bg-slate-800 border border-slate-700 text-white placeholder-slate-500 px-5 py-3.5 pr-14 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 min-h-[56px] max-h-32 text-sm shadow-sm transition-all"
                            rows={1}
                        />
                        <button
                            onClick={() => handleSend(input)}
                            disabled={!input.trim() || loading}
                            className="absolute right-2 bottom-2 p-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-500 disabled:opacity-50 disabled:hover:bg-indigo-600 transition-colors shadow-lg shadow-indigo-600/20"
                        >
                            <Send className="w-4 h-4" />
                        </button>
                    </div>
                    <div className="text-center mt-3">
                        <span className="text-xs text-slate-500 font-medium">FinSage AI Copilot can make mistakes. Verify critical financial data.</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

const MessageBubble = ({ msg, fetchPendingActions }) => {
    const isUser = msg.role === 'user';
    const [sourcesOpen, setSourcesOpen] = useState(false);

    return (
        <div className={`flex gap-4 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 shadow-sm ${isUser ? 'bg-indigo-600 text-white' : 'bg-slate-700 border border-slate-600 text-white'}`}>
                {isUser ? <span className="font-medium text-xs">US</span> : <ShieldAlert className="w-4 h-4 text-indigo-400" />}
            </div>
            
            <div className={`max-w-[85%] flex flex-col gap-3 ${isUser ? 'items-end' : 'items-start'}`}>
                {/* Main Content Bubble */}
                <div className={`p-5 rounded-2xl shadow-sm text-sm leading-relaxed ${isUser ? 'bg-indigo-600 text-white rounded-tr-none' : 'bg-slate-800/80 border border-slate-700 text-slate-200 rounded-tl-none'}`}>
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                </div>
                
                {/* Assistant Metadata (Guardrails, Actions, Sources) */}
                {!isUser && (
                    <div className="w-full space-y-3 mt-0.5">
                        {/* Guardrail Badge */}
                        {msg.low_confidence && (
                            <div className="inline-flex items-center px-3 py-1.5 bg-rose-500/10 text-rose-400 border border-rose-500/20 rounded-md text-xs font-semibold uppercase tracking-wider">
                                <span className="w-1.5 h-1.5 rounded-full bg-rose-500 mr-2 animate-pulse"></span>
                                Low Confidence: No verifiable tool data found.
                            </div>
                        )}

                        {/* Actions / Downloads */}
                        {msg.actions && msg.actions.map((action, i) => {
                            if (action.type === 'report_generated') {
                                return (
                                    <a key={i} href={`http://localhost:8000${action.url}`} download className="flex items-center justify-between p-4 bg-slate-800 border border-emerald-500/30 rounded-xl hover:bg-slate-700 transition-colors w-full max-w-sm cursor-pointer group no-underline shadow-lg shadow-emerald-500/5">
                                        <div className="flex items-center gap-3">
                                            <div className="p-2.5 bg-emerald-500/10 rounded-lg text-emerald-400 border border-emerald-500/20 group-hover:bg-emerald-500/20 transition-colors">
                                                <FileText className="w-5 h-5" />
                                            </div>
                                            <div>
                                                <p className="text-sm font-semibold text-emerald-400 tracking-wide">Formal Risk Report</p>
                                                <p className="text-xs text-slate-400 mt-0.5">PDF Document Ready</p>
                                            </div>
                                        </div>
                                        <Download className="w-5 h-5 text-emerald-500/70 group-hover:text-emerald-400 transition-colors" />
                                    </a>
                                );
                            } else if (action.type === 'proposed_action') {
                                return <ProposalCard key={i} action={action} fetchPendingActions={fetchPendingActions} />;
                            }
                            return null;
                        })}

                        {/* Transparency Panel (Sources) */}
                        {msg.specialists_used && msg.specialists_used.length > 0 && (
                            <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden w-full max-w-md shadow-sm">
                                <button 
                                    onClick={() => setSourcesOpen(!sourcesOpen)}
                                    className="w-full px-4 py-3 flex items-center justify-between text-xs font-medium text-slate-300 hover:bg-slate-700/50 transition-colors focus:outline-none"
                                >
                                    <span className="flex items-center gap-2">
                                        <CheckCircle className="w-4 h-4 text-emerald-400" />
                                        Routing: {msg.specialists_used.join(' → ')}
                                    </span>
                                    {sourcesOpen ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
                                </button>
                                
                                {sourcesOpen && msg.sources && msg.sources.length > 0 && (
                                    <div className="px-4 pb-4 pt-1 border-t border-slate-700/50 bg-slate-800/30">
                                        {msg.sources.map((src, i) => (
                                            <div key={i} className="mb-3 last:mb-0 mt-2">
                                                <div className="text-[11px] font-mono text-indigo-400 font-semibold mb-1">
                                                    &gt; {src.tool}()
                                                </div>
                                                <div className="text-[11px] font-mono text-slate-400 bg-slate-900/50 p-2 rounded-md border border-slate-700 break-words">
                                                    {JSON.stringify(src.params)}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                                {sourcesOpen && (!msg.sources || msg.sources.length === 0) && (
                                    <div className="px-4 pb-4 pt-3 border-t border-slate-700/50 bg-slate-800/30 text-xs text-slate-500 italic">
                                        No specific data tools were called.
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

const ProposalCard = ({ action, fetchPendingActions }) => {
    const [status, setStatus] = useState('pending');

    const handleApprove = async () => {
        try {
            await fetch(`http://localhost:8000/api/actions/${action.proposal_id}/approve`, { method: 'POST' });
            setStatus('approved');
            fetchPendingActions();
        } catch (err) {
            console.error("Failed to approve", err);
        }
    };

    const handleReject = async () => {
        try {
            await fetch(`http://localhost:8000/api/actions/${action.proposal_id}/reject`, { method: 'POST' });
            setStatus('rejected');
            fetchPendingActions();
        } catch (err) {
            console.error("Failed to reject", err);
        }
    };

    if (status === 'approved') {
        return (
            <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl w-full max-w-sm mt-2">
                <div className="flex items-center gap-2 mb-1">
                    <CheckCircle className="w-4 h-4 text-emerald-400" />
                    <span className="text-sm font-semibold text-emerald-400">Action Executed</span>
                </div>
                <p className="text-xs text-emerald-300/80">
                    {action.action_type.replace(/_/g, ' ')} for {action.target_entity_id}
                </p>
            </div>
        );
    }

    if (status === 'rejected') {
        return (
            <div className="p-4 bg-slate-800 border border-slate-700 rounded-xl w-full max-w-sm mt-2 opacity-60">
                <div className="flex items-center gap-2 mb-1">
                    <X className="w-4 h-4 text-slate-400" />
                    <span className="text-sm font-semibold text-slate-400">Action Rejected</span>
                </div>
                <p className="text-xs text-slate-500">
                    {action.action_type.replace(/_/g, ' ')} for {action.target_entity_id}
                </p>
            </div>
        );
    }

    return (
        <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl w-full max-w-sm mt-2 shadow-lg shadow-amber-500/5">
            <div className="flex items-center gap-2 mb-3">
                <ClipboardList className="w-5 h-5 text-amber-400" />
                <span className="text-sm font-bold text-amber-400 tracking-wide uppercase">Action Proposal</span>
            </div>
            
            <div className="bg-slate-900/50 p-3 rounded-lg border border-amber-500/20 mb-4 space-y-2">
                <div className="flex justify-between items-center">
                    <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Action</span>
                    <span className="text-[11px] font-bold text-slate-200">{action.action_type.replace(/_/g, ' ')}</span>
                </div>
                <div className="flex justify-between items-center">
                    <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Target</span>
                    <span className="text-[11px] font-bold text-slate-200">{action.target_entity_id}</span>
                </div>
                <div className="mt-2 text-[11px] text-slate-300 italic pt-2 border-t border-slate-700">
                    {action.description}
                </div>
            </div>

            <div className="flex gap-3">
                <button 
                    onClick={handleApprove}
                    className="flex-1 py-2 bg-amber-500 hover:bg-amber-400 text-slate-900 font-bold rounded-lg text-xs transition-colors shadow-lg shadow-amber-500/20 flex items-center justify-center gap-1.5"
                >
                    <Check className="w-3.5 h-3.5" /> Approve
                </button>
                <button 
                    onClick={handleReject}
                    className="flex-1 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold rounded-lg text-xs transition-colors border border-slate-600 flex items-center justify-center gap-1.5"
                >
                    <X className="w-3.5 h-3.5" /> Reject
                </button>
            </div>
        </div>
    );
};

export default ChatInterface;
