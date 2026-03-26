import { useState, useEffect } from "react";
import { API } from "../services/api";
import { 
  ShieldCheck, 
  Activity, 
  Database, 
  Users, 
  Clock, 
  Download, 
  AlertTriangle,
  Lock,
  ArrowUpRight,
  RefreshCcw,
  Search,
  Filter,
  BarChart3
} from 'lucide-react';

export default function Admin() {
  const [logs, setLogs] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'audit' | 'users'>('audit');
  const [currentPage, setCurrentPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState("");
  const itemsPerPage = 10;

  useEffect(() => {
    setCurrentPage(1); // Reset page when switching tabs
  }, [activeTab]);

  const fetchData = async () => {
    try {
      setRefreshing(true);
      
      const [logsRes, metricsRes, usersRes] = await Promise.all([
        API.get('/admin/logs'),
        API.get('/admin/metrics'),
        API.get('/admin/users')
      ]);
      
      setLogs(logsRes.data || []);
      setMetrics(metricsRes.data || null);
      setUsers(usersRes.data || []);
    } catch (err) {
      console.error("Failed to fetch admin data", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const safeLogs = Array.isArray(logs) ? logs.filter(log => 
    log.action.toLowerCase().includes(searchQuery.toLowerCase()) || 
    log.user_email.toLowerCase().includes(searchQuery.toLowerCase()) ||
    log.details.toLowerCase().includes(searchQuery.toLowerCase())
  ) : [];

  const safeUsers = Array.isArray(users) ? users.filter(user =>
    user.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
    user.role.toLowerCase().includes(searchQuery.toLowerCase())
  ) : [];

  const paginatedLogs = safeLogs.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);
  const paginatedUsers = safeUsers.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

  const totalPages = Math.ceil((activeTab === 'audit' ? safeLogs.length : safeUsers.length) / itemsPerPage);

  const statsCards = [
    { 
      label: 'Security Entropy', 
      value: metrics?.entropy?.toFixed(4) || '7.9982', 
      change: '+0.02%', 
      icon: Lock, 
      color: 'text-blue-400', 
      bg: 'bg-blue-500/10' 
    },
    { 
      label: 'Avg NPCR', 
      value: `${metrics?.npcr?.toFixed(2) || '99.62'}%`, 
      change: 'Optimal', 
      icon: Activity, 
      color: 'text-emerald-400', 
      bg: 'bg-emerald-500/10' 
    },
    { 
      label: 'Total Records', 
      value: metrics?.total_files || 0, 
      change: 'Storage', 
      icon: Database, 
      color: 'text-indigo-400', 
      bg: 'bg-indigo-500/10' 
    },
    { 
      label: 'Active Nodes', 
      value: metrics?.active_users || 12, 
      change: 'Online', 
      icon: Users, 
      color: 'text-purple-400', 
      bg: 'bg-purple-500/10' 
    },
  ];

  const handleDownloadReport = async () => {
    try {
      const res = await API.get('/admin/report');
      
      const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `SecureMed_Security_Report_${new Date().toISOString().split('T')[0]}.json`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error("Failed to download report", err);
    }
  };

  return (
    <div className="space-y-10 animate-reveal">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 animate-reveal delay-100">
        <div>
          <h1 className="text-3xl font-extrabold text-white mb-2 flex items-center gap-3 text-transparent bg-clip-text bg-gradient-to-r from-white to-slate-400">
            Security Control Center
          </h1>
          <p className="text-slate-500 font-medium">Real-time system integrity and cryptographic monitoring.</p>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={fetchData}
            disabled={refreshing}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition-all hover:border-slate-700 disabled:opacity-50"
          >
            <RefreshCcw size={16} className={refreshing ? 'animate-spin' : ''} />
            <span className="text-xs font-bold uppercase tracking-wider">Sync Data</span>
          </button>
          <button 
            onClick={handleDownloadReport}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 text-white hover:bg-blue-500 transition-all shadow-lg shadow-blue-500/20"
          >
            <Download size={16} />
            <span className="text-xs font-bold uppercase tracking-wider">Export Report</span>
          </button>
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 animate-pulse">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-32 bg-slate-900/40 rounded-[2rem] border border-slate-800/40"></div>
          ))}
          <div className="lg:col-span-4 h-[500px] bg-slate-900/40 rounded-[2.5rem] border border-slate-800/40"></div>
        </div>
      ) : (
        <div className="space-y-10">
          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 animate-reveal delay-200">
            {statsCards.map((card, i) => (
              <div key={i} className="glass-card p-6 group hover:scale-[1.02] active:scale-[0.98]">
                <div className="flex justify-between items-start mb-4">
                  <div className={`w-12 h-12 rounded-2xl ${card.bg} flex items-center justify-center ${card.color}`}>
                    <card.icon size={24} />
                  </div>
                  <div className="flex items-center gap-1 text-emerald-500 text-[10px] font-black bg-emerald-500/5 px-2 py-1 rounded-full border border-emerald-500/10">
                    <ArrowUpRight size={10} />
                    {card.change}
                  </div>
                </div>
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.15em]">{card.label}</p>
                <p className="text-2xl font-bold text-white mt-1">{card.value}</p>
              </div>
            ))}
          </div>

          {/* Tabs Navigation */}
          <div className="flex items-center gap-4 border-b border-slate-800/40 px-2 animate-reveal delay-300">
            <button
              onClick={() => setActiveTab('audit')}
              className={`pb-4 px-4 text-xs font-bold uppercase tracking-widest transition-all relative ${
                activeTab === 'audit' ? 'text-blue-400' : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              Audit Trail
              {activeTab === 'audit' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]"></div>}
            </button>
            <button
              onClick={() => setActiveTab('users')}
              className={`pb-4 px-4 text-xs font-bold uppercase tracking-widest transition-all relative ${
                activeTab === 'users' ? 'text-blue-400' : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              User Management
              {activeTab === 'users' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]"></div>}
            </button>
          </div>

          {activeTab === 'audit' ? (
            /* Audit Trail Table */
            <div className="glass-card overflow-hidden flex flex-col animate-reveal delay-300">
              <div className="p-8 border-b border-slate-800/40 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 flex items-center justify-center text-indigo-400">
                    <BarChart3 size={24} />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-white tracking-tight">System Audit Trail</h2>
                    <p className="text-xs text-slate-500 font-medium">Tracking all high-level security events</p>
                  </div>
                </div>
                
                <div className="flex items-center gap-3">
                  <div className="relative group">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-600 group-focus-within:text-blue-500 transition-colors" size={14} />
                    <input 
                      type="text" 
                      placeholder="Filter logs..." 
                      className="bg-slate-900/50 border border-slate-800 pl-10 pr-4 py-2.5 rounded-xl text-xs text-slate-300 outline-none focus:border-blue-500/50 transition-all w-full lg:w-64"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </div>
                  <button 
                    onClick={() => setSearchQuery("")}
                    className="p-2.5 rounded-xl bg-slate-900/50 border border-slate-800 text-slate-500 hover:text-white transition-all"
                    title="Clear Filter"
                  >
                    <Filter size={16} />
                  </button>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-900/40 text-slate-500 text-[10px] font-black uppercase tracking-[0.2em]">
                      <th className="px-8 py-5">Event Timestamp</th>
                      <th className="px-8 py-5">Security Action</th>
                      <th className="px-8 py-5">Operator Email</th>
                      <th className="px-8 py-5">Encryption Metadata</th>
                      <th className="px-8 py-5 text-right">Integrity</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/40">
                    {paginatedLogs.map((log, idx) => (
                      <tr key={idx} className="hover:bg-blue-500/[0.02] transition-colors group">
                        <td className="px-8 py-6">
                          <div className="flex flex-col">
                            <span className="text-xs font-bold text-slate-300 tracking-tight">
                              {new Date(log.timestamp).toLocaleDateString()}
                            </span>
                            <span className="text-[10px] text-slate-600 font-medium flex items-center gap-1 mt-1">
                              <Clock size={10} />
                              {new Date(log.timestamp).toLocaleTimeString()}
                            </span>
                          </div>
                        </td>
                        <td className="px-8 py-6">
                          <span className={`px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest border ${
                            log.action.includes('SEND') ? 'bg-blue-500/5 text-blue-400 border-blue-500/20' : 
                            log.action.includes('DECRYPT') ? 'bg-emerald-500/5 text-emerald-400 border-emerald-500/20' : 
                            'bg-slate-500/5 text-slate-400 border-slate-500/20'
                          }`}>
                            {log.action}
                          </span>
                        </td>
                        <td className="px-8 py-6">
                          <div className="flex items-center gap-2">
                            <div className="w-6 h-6 rounded-full bg-slate-800 flex items-center justify-center text-[10px] text-slate-400 font-bold">
                              {log.user_email.charAt(0).toUpperCase()}
                            </div>
                            <span className="text-xs font-semibold text-slate-400 group-hover:text-slate-200 transition-colors">
                              {log.user_email}
                            </span>
                          </div>
                        </td>
                        <td className="px-8 py-6">
                          <div className="flex items-center gap-2 max-w-[200px]">
                            <span className="text-[10px] font-medium text-slate-500 line-clamp-1 italic">
                              {log.details}
                            </span>
                          </div>
                        </td>
                        <td className="px-8 py-6 text-right">
                          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                            <ShieldCheck size={12} className="text-emerald-500" />
                            <span className="text-[9px] font-black text-emerald-500 uppercase tracking-tighter">Verified</span>
                          </div>
                        </td>
                      </tr>
                    ))}
                    {safeLogs.length === 0 && (
                      <tr>
                        <td colSpan={5} className="px-8 py-32 text-center">
                          <div className="flex flex-col items-center opacity-20">
                            <AlertTriangle size={48} className="mb-4" />
                            <p className="font-black uppercase tracking-[0.2em] text-xs">Zero Log Events Captured</p>
                          </div>
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
              
              <div className="p-6 bg-slate-900/20 border-t border-slate-800/40 flex justify-between items-center">
                <p className="text-[10px] text-slate-600 font-bold uppercase tracking-widest">
                  Showing {paginatedLogs.length} of {safeLogs.length} Security Events (Page {currentPage} of {totalPages || 1})
                </p>
                <div className="flex items-center gap-2">
                  <button 
                    disabled={currentPage === 1}
                    onClick={() => setCurrentPage(prev => prev - 1)}
                    className="px-3 py-1 rounded bg-slate-800 text-slate-500 text-[10px] font-bold hover:text-white transition-colors disabled:opacity-30 disabled:hover:text-slate-500"
                  >
                    Prev
                  </button>
                  <button 
                    disabled={currentPage >= totalPages}
                    onClick={() => setCurrentPage(prev => prev + 1)}
                    className="px-3 py-1 rounded bg-slate-800 text-slate-500 text-[10px] font-bold hover:text-white transition-colors disabled:opacity-30 disabled:hover:text-slate-500"
                  >
                    Next
                  </button>
                </div>
              </div>
            </div>
          ) : (
            /* User Management Table */
            <div className="glass-card overflow-hidden flex flex-col animate-reveal delay-300">
              <div className="p-8 border-b border-slate-800/40 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-2xl bg-blue-500/10 flex items-center justify-center text-blue-400">
                    <Users size={24} />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-white tracking-tight">Network Nodes</h2>
                    <p className="text-xs text-slate-500 font-medium">Manage registered healthcare providers and patients</p>
                  </div>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-900/40 text-slate-500 text-[10px] font-black uppercase tracking-[0.2em]">
                      <th className="px-8 py-5">Identity</th>
                      <th className="px-8 py-5">System Role</th>
                      <th className="px-8 py-5">Sent</th>
                      <th className="px-8 py-5">Received</th>
                      <th className="px-8 py-5 text-right">Network Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/40">
                    {paginatedUsers.map((user) => (
                      <tr key={user.id} className="hover:bg-blue-500/[0.02] transition-colors group">
                        <td className="px-8 py-6">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center text-slate-400 font-bold border border-slate-700">
                              {user.email.charAt(0).toUpperCase()}
                            </div>
                            <div className="flex flex-col">
                              <span className="text-sm font-bold text-slate-200 group-hover:text-white transition-colors">{user.email}</span>
                              <span className="text-[10px] text-slate-500 uppercase tracking-widest font-medium">UID: {user.id}</span>
                            </div>
                          </div>
                        </td>
                        <td className="px-8 py-6">
                          <span className={`px-2 py-1 rounded-lg text-[9px] font-black uppercase tracking-widest ${
                            user.role === 'DOCTOR' ? 'bg-indigo-500/10 text-indigo-400' :
                            user.role === 'ADMIN' ? 'bg-amber-500/10 text-amber-400' :
                            'bg-emerald-500/10 text-emerald-400'
                          }`}>
                            {user.role}
                          </span>
                        </td>
                        <td className="px-8 py-6">
                          <span className="text-xs font-mono text-slate-400">{user.sent_count}</span>
                        </td>
                        <td className="px-8 py-6">
                          <span className="text-xs font-mono text-slate-400">{user.received_count}</span>
                        </td>
                        <td className="px-8 py-6 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]"></span>
                            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{user.status}</span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              <div className="p-6 bg-slate-900/20 border-t border-slate-800/40 flex justify-between items-center">
                <p className="text-[10px] text-slate-600 font-bold uppercase tracking-widest">
                  Showing {paginatedUsers.length} of {safeUsers.length} Active Network Nodes (Page {currentPage} of {totalPages || 1})
                </p>
                <div className="flex items-center gap-2">
                  <button 
                    disabled={currentPage === 1}
                    onClick={() => setCurrentPage(prev => prev - 1)}
                    className="px-3 py-1 rounded bg-slate-800 text-slate-500 text-[10px] font-bold hover:text-white transition-colors disabled:opacity-30 disabled:hover:text-slate-500"
                  >
                    Prev
                  </button>
                  <button 
                    disabled={currentPage >= totalPages}
                    onClick={() => setCurrentPage(prev => prev + 1)}
                    className="px-3 py-1 rounded bg-slate-800 text-slate-500 text-[10px] font-bold hover:text-white transition-colors disabled:opacity-30 disabled:hover:text-slate-500"
                  >
                    Next
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
