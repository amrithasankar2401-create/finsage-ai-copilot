import React, { useState, useEffect } from 'react';
import { ShieldCheck, AlertTriangle, Activity, Database, ArrowLeft, ShieldAlert, Cpu, ClipboardList, CheckCircle } from 'lucide-react';

const AdminDashboard = () => {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [briefings, setBriefings] = useState([]);
    const [pendingActions, setPendingActions] = useState([]);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const resLogs = await fetch('http://localhost:8000/api/admin/logs');
                const dataLogs = await resLogs.json();
                setLogs(dataLogs);

                const resBrief = await fetch('http://localhost:8000/api/briefings/history');
                const dataBrief = await resBrief.json();
                if (Array.isArray(dataBrief)) {
                    setBriefings(dataBrief.slice(0, 3)); // Get last 3
                } else {
                    setBriefings([]);
                }

                const resActions = await fetch('http://localhost:8000/api/actions/pending');
                const dataActions = await resActions.json();
                setPendingActions(dataActions);
            } catch (err) {
                console.error("Failed to fetch admin data", err);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    // Separating autonomous scans from user chats
    const chatLogs = logs.filter(l => l.event_type !== 'autonomous_scan' && !l.event_type?.startsWith('action_'));
    const autoLogs = logs.filter(l => l.event_type === 'autonomous_scan');
    const actionLogs = logs.filter(l => l.event_type?.startsWith('action_'));

    const totalQueries = chatLogs.length;
    const lowConfidenceCount = chatLogs.filter(l => l.low_confidence).length;
    const autonomousScans = autoLogs.length;
    
    // Calculate compound alerts from autonomous scans
    const compoundAlerts = autoLogs.reduce((acc, curr) => {
        const action = curr.actions?.find(a => a.type === 'autonomous_scan_completed');
        return acc + (action?.compound_alerts_count || 0);
    }, 0);
    
    const toolsUsed = chatLogs.flatMap(l => l.tools_called?.map(t => t.tool) || []);
    const topThemes = toolsUsed.reduce((acc, curr) => {
        acc[curr] = (acc[curr] || 0) + 1;
        return acc;
    }, {});
    
    const maxToolCount = Object.values(topThemes).length > 0 ? Math.max(...Object.values(topThemes)) : 1;

    const specialistsUsedList = chatLogs.flatMap(l => l.specialists_used || []);
    const topSpecialists = specialistsUsedList.reduce((acc, curr) => {
        acc[curr] = (acc[curr] || 0) + 1;
        return acc;
    }, {});
    const maxSpecialistCount = Object.values(topSpecialists).length > 0 ? Math.max(...Object.values(topSpecialists)) : 1;

    return (
        <div className="min-h-screen bg-slate-900 text-slate-200 font-sans">
            {/* Sticky Header */}
            <div className="sticky top-0 z-10 bg-slate-900/95 backdrop-blur border-b border-slate-800">
                <div className="max-w-7xl mx-auto px-8 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="bg-indigo-500/20 p-2 rounded-lg border border-indigo-500/30">
                            <ShieldCheck className="w-6 h-6 text-indigo-400" />
                        </div>
                        <div>
                            <h1 className="text-xl font-bold text-white tracking-wide">LLM Governance & Audit Console</h1>
                            <p className="text-xs text-slate-400 mt-0.5 font-medium uppercase tracking-wider">SOX Compliance Monitoring</p>
                        </div>
                    </div>
                    <a href="/" className="flex items-center gap-2 text-sm font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 px-4 py-2 rounded-lg transition-colors no-underline">
                        <ArrowLeft className="w-4 h-4" />
                        Back to Copilot
                    </a>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-8 py-8 space-y-8">
                
                {/* Copilot KPIs */}
                <div>
                    <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">Reactive User Interactions</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
                        {/* Card 1 */}
                        <div className="bg-slate-800/50 p-6 rounded-xl border border-slate-700 border-l-4 border-l-indigo-500 shadow-lg flex flex-col">
                            <div className="flex items-center gap-3 mb-4">
                                <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-lg">
                                    <Activity className="w-5 h-5" />
                                </div>
                                <h3 className="font-semibold text-slate-300 text-sm uppercase tracking-wider">Total Interactions</h3>
                            </div>
                            <p className="text-4xl font-bold text-white">{totalQueries}</p>
                        </div>
                        
                        {/* Card 2 */}
                        <div className="bg-slate-800/50 p-6 rounded-xl border border-slate-700 border-l-4 border-l-rose-500 shadow-lg flex flex-col">
                            <div className="flex items-center gap-3 mb-4">
                                <div className="p-2 bg-rose-500/10 text-rose-400 rounded-lg">
                                    <AlertTriangle className="w-5 h-5" />
                                </div>
                                <h3 className="font-semibold text-slate-300 text-sm uppercase tracking-wider">Low Confidence Flags</h3>
                            </div>
                            <div className="flex items-end gap-3">
                                <p className="text-4xl font-bold text-rose-400">{lowConfidenceCount}</p>
                                <p className="text-xs text-rose-500/70 mb-1 font-medium">unverified responses</p>
                            </div>
                        </div>

                        {/* Card 3 (Bar Chart) */}
                        <div className="bg-slate-800/50 p-6 rounded-xl border border-slate-700 border-l-4 border-l-emerald-500 shadow-lg flex flex-col justify-between">
                            <div className="flex items-center gap-3 mb-4">
                                <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg">
                                    <Database className="w-5 h-5" />
                                </div>
                                <h3 className="font-semibold text-slate-300 text-sm uppercase tracking-wider">Most Used Tools</h3>
                            </div>
                            <div className="space-y-3 mt-2">
                                {Object.entries(topThemes).slice(0, 3).map(([tool, count]) => (
                                    <div key={tool} className="relative w-full">
                                        <div className="flex justify-between text-xs mb-1">
                                            <span className="font-mono text-slate-300 truncate pr-2">{tool}</span>
                                            <span className="font-semibold text-emerald-400">{count}</span>
                                        </div>
                                        <div className="w-full bg-slate-700 rounded-full h-1.5 overflow-hidden">
                                            <div 
                                                className="bg-emerald-500 h-1.5 rounded-full" 
                                                style={{ width: `${(count / maxToolCount) * 100}%` }}
                                            ></div>
                                        </div>
                                    </div>
                                ))}
                                {Object.keys(topThemes).length === 0 && <span className="text-sm text-slate-500 italic">No tools executed yet.</span>}
                            </div>
                        </div>

                        {/* Card 4 (Bar Chart for Specialists) */}
                        <div className="bg-slate-800/50 p-6 rounded-xl border border-slate-700 border-l-4 border-l-sky-500 shadow-lg flex flex-col justify-between">
                            <div className="flex items-center gap-3 mb-4">
                                <div className="p-2 bg-sky-500/10 text-sky-400 rounded-lg">
                                    <ShieldCheck className="w-5 h-5" />
                                </div>
                                <h3 className="font-semibold text-slate-300 text-sm uppercase tracking-wider">Specialist Utilization</h3>
                            </div>
                            <div className="space-y-3 mt-2">
                                {Object.entries(topSpecialists).slice(0, 3).map(([spec, count]) => (
                                    <div key={spec} className="relative w-full">
                                        <div className="flex justify-between text-xs mb-1">
                                            <span className="font-mono text-slate-300 truncate pr-2">{spec}</span>
                                            <span className="font-semibold text-sky-400">{count}</span>
                                        </div>
                                        <div className="w-full bg-slate-700 rounded-full h-1.5 overflow-hidden">
                                            <div 
                                                className="bg-sky-500 h-1.5 rounded-full" 
                                                style={{ width: `${(count / maxSpecialistCount) * 100}%` }}
                                            ></div>
                                        </div>
                                    </div>
                                ))}
                                {Object.keys(topSpecialists).length === 0 && <span className="text-sm text-slate-500 italic">No agents executed yet.</span>}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Autonomous KPIs */}
                <div>
                    <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4 mt-4">Proactive Background Scanning</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="bg-slate-800/50 p-6 rounded-xl border border-slate-700 border-l-4 border-l-violet-500 shadow-lg flex items-center justify-between">
                            <div>
                                <div className="flex items-center gap-3 mb-2">
                                    <div className="p-1.5 bg-violet-500/10 text-violet-400 rounded-lg">
                                        <Cpu className="w-4 h-4" />
                                    </div>
                                    <h3 className="font-semibold text-slate-300 text-xs uppercase tracking-wider">Autonomous Scans Executed</h3>
                                </div>
                                <p className="text-xs text-slate-500">Scheduled background jobs</p>
                            </div>
                            <p className="text-3xl font-bold text-violet-400">{autonomousScans}</p>
                        </div>
                        
                        <div className="bg-slate-800/50 p-6 rounded-xl border border-slate-700 border-l-4 border-l-amber-500 shadow-lg flex items-center justify-between">
                            <div>
                                <div className="flex items-center gap-3 mb-2">
                                    <div className="p-1.5 bg-amber-500/10 text-amber-400 rounded-lg">
                                        <AlertTriangle className="w-4 h-4" />
                                    </div>
                                    <h3 className="font-semibold text-slate-300 text-xs uppercase tracking-wider">Total Compound Alerts</h3>
                                </div>
                                <p className="text-xs text-slate-500">Multi-domain risk anomalies detected</p>
                            </div>
                            <p className="text-3xl font-bold text-amber-400">{compoundAlerts}</p>
                        </div>
                    </div>
                </div>

                {/* HITL Action Workflow KPIs */}
                <div>
                    <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4 mt-4">Human-in-the-Loop Actions</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="bg-slate-800/50 p-6 rounded-xl border border-slate-700 border-l-4 border-l-amber-500 shadow-lg flex items-center justify-between">
                            <div>
                                <div className="flex items-center gap-3 mb-2">
                                    <div className="p-1.5 bg-amber-500/10 text-amber-400 rounded-lg">
                                        <ClipboardList className="w-4 h-4" />
                                    </div>
                                    <h3 className="font-semibold text-slate-300 text-xs uppercase tracking-wider">Actions Pending Approval</h3>
                                </div>
                                <p className="text-xs text-slate-500">Awaiting human review</p>
                            </div>
                            <p className="text-3xl font-bold text-amber-400">{pendingActions.length}</p>
                        </div>
                        
                        <div className="bg-slate-800/50 p-6 rounded-xl border border-slate-700 border-l-4 border-l-emerald-500 shadow-lg flex items-center justify-between">
                            <div>
                                <div className="flex items-center gap-3 mb-2">
                                    <div className="p-1.5 bg-emerald-500/10 text-emerald-400 rounded-lg">
                                        <CheckCircle className="w-4 h-4" />
                                    </div>
                                    <h3 className="font-semibold text-slate-300 text-xs uppercase tracking-wider">Actions Executed</h3>
                                </div>
                                <p className="text-xs text-slate-500">Approved and executed successfully</p>
                            </div>
                            <p className="text-3xl font-bold text-emerald-400">{actionLogs.filter(l => l.event_type === 'action_approved_executed').length}</p>
                        </div>
                    </div>
                </div>

                {/* Interaction Log Table */}
                <div className="bg-slate-800/50 rounded-xl border border-slate-700 shadow-lg overflow-hidden">
                    <div className="px-6 py-5 border-b border-slate-700 bg-slate-800/80">
                        <h2 className="font-semibold text-white flex items-center gap-2">
                            <ShieldAlert className="w-4 h-4 text-slate-400" />
                            Unified Audit Log (Reactive & Proactive)
                        </h2>
                    </div>
                    {loading ? (
                        <div className="p-12 text-center text-slate-500 animate-pulse">Synchronizing SOX logs...</div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full text-left text-sm text-slate-300">
                                <thead className="bg-slate-900/50 text-xs uppercase text-slate-500 font-semibold tracking-wider">
                                    <tr>
                                        <th className="px-6 py-4">Timestamp</th>
                                        <th className="px-6 py-4">Event Type</th>
                                        <th className="px-6 py-4">Prompt / Action</th>
                                        <th className="px-6 py-4">Risk Flag</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-700/50">
                                    {logs.map((log, idx) => {
                                        const isAuto = log.event_type === 'autonomous_scan';
                                        return (
                                        <tr key={idx} className="hover:bg-slate-700/30 transition-colors even:bg-slate-800/30">
                                            <td className="px-6 py-4 whitespace-nowrap font-mono text-xs text-slate-400">
                                                {new Date(log.timestamp).toLocaleString()}
                                            </td>
                                            <td className="px-6 py-4">
                                                {isAuto ? (
                                                    <span className="px-2 py-1 bg-violet-500/10 text-violet-400 border border-violet-500/20 rounded-md text-[10px] font-bold uppercase">Background Scan</span>
                                                ) : log.event_type?.startsWith('action_') ? (
                                                    <span className="px-2 py-1 bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded-md text-[10px] font-bold uppercase">System Action</span>
                                                ) : (
                                                    <span className="px-2 py-1 bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded-md text-[10px] font-bold uppercase">User Chat</span>
                                                )}
                                            </td>
                                            <td className="px-6 py-4 max-w-sm truncate text-slate-200" title={log.user_message || log.assistant_response}>
                                                {log.event_type?.startsWith('action_') ? log.assistant_response : log.user_message}
                                            </td>
                                            <td className="px-6 py-4">
                                                {isAuto ? (
                                                    <span className="inline-flex items-center px-2.5 py-1 bg-slate-700 text-slate-400 rounded-full text-[10px] font-semibold uppercase tracking-wider">
                                                        N/A
                                                    </span>
                                                ) : log.event_type === 'action_proposed' ? (
                                                    <span className="inline-flex items-center px-2.5 py-1 bg-amber-500/10 border border-amber-500/20 text-amber-400 rounded-full text-xs font-semibold uppercase tracking-wider">
                                                        Proposed
                                                    </span>
                                                ) : log.event_type === 'action_approved_executed' ? (
                                                    <span className="inline-flex items-center px-2.5 py-1 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-full text-xs font-semibold uppercase tracking-wider">
                                                        Executed
                                                    </span>
                                                ) : log.event_type === 'action_rejected' ? (
                                                    <span className="inline-flex items-center px-2.5 py-1 bg-slate-800 border border-slate-700 text-slate-500 rounded-full text-xs font-semibold uppercase tracking-wider">
                                                        Rejected
                                                    </span>
                                                ) : log.low_confidence ? (
                                                    <span className="inline-flex items-center px-2.5 py-1 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-full text-xs font-semibold uppercase tracking-wider">
                                                        <span className="w-1.5 h-1.5 rounded-full bg-rose-500 mr-1.5 animate-pulse"></span>
                                                        Flagged
                                                    </span>
                                                ) : (
                                                    <span className="inline-flex items-center px-2.5 py-1 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-full text-xs font-semibold uppercase tracking-wider">
                                                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5"></span>
                                                        Safe
                                                    </span>
                                                )}
                                            </td>
                                        </tr>
                                    )})}
                                    {logs.length === 0 && (
                                        <tr>
                                            <td colSpan="4" className="px-6 py-12 text-center text-slate-500">
                                                No interaction logs found. System is ready.
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>

            </div>
        </div>
    );
};

export default AdminDashboard;
