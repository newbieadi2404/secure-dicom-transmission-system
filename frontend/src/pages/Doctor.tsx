import { useState, useRef, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { sendDoctorFile, getDoctorRecords, getDoctorPatients, revokeDoctorRecord, getDoctorInbox, decryptDoctorFile } from "../services/api";
import { 
  Upload, 
  Send, 
  FileText, 
  History, 
  Users, 
  CheckCircle, 
  AlertCircle,
  FileDigit,
  Shield,
  FileUp,
  ArrowRight,
  User,
  Clock,
  X,
  Trash2
} from 'lucide-react';

export default function Doctor() {
  const { token } = useAuth();
  const [email, setEmail] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [bodyPart, setBodyPart] = useState("Head");
  const [priority, setPriority] = useState("NORMAL");
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [recentRecords, setRecentRecords] = useState<any[]>([]);
  const [inboxRecords, setInboxRecords] = useState<any[]>([]);
  const [patients, setPatients] = useState<any[]>([]);
  const [fetchingRecords, setFetchingRecords] = useState(false);
  const [activeTab, setActiveTab] = useState<'transfer' | 'patients' | 'inbox'>('transfer');
  const [selectedRecord, setSelectedRecord] = useState<any | null>(null);
  const [selectedPatient, setSelectedPatient] = useState<any | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const fetchDashboardData = async () => {
    try {
      setFetchingRecords(true);
      const [recordsRes, patientsRes, inboxRes] = await Promise.all([
        getDoctorRecords(),
        getDoctorPatients(),
        getDoctorInbox()
      ]);
      setRecentRecords(recordsRes.data || []);
      setPatients(patientsRes.data || []);
      setInboxRecords(inboxRes.data || []);
    } catch (err) {
      console.error("Failed to fetch doctor dashboard data", err);
    } finally {
      setFetchingRecords(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleSend = async () => {
    setMessage("");
    if (!token) {
      setMessage("You must be logged in to send files.");
      return;
    }

    if (!email || !file) {
      setMessage("Enter email and select a file");
      return;
    }

    try {
      setLoading(true);

      const formData = new FormData();
      formData.append("patient_email", email);
      formData.append("file", file);
      formData.append("body_part", bodyPart);
      formData.append("priority", priority);
      formData.append("clinical_notes", notes);

      await sendDoctorFile(formData);

      setMessage("✅ Record transmitted successfully via hybrid tunnel.");
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      setEmail("");
      setNotes("");
      fetchDashboardData(); // Refresh everything
    } catch (err: any) {
      const msg = err?.response?.data?.error || err?.message || "Transmission failure";
      setMessage(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleRevoke = async (recordId: number) => {
    if (!window.confirm("Are you sure you want to revoke this record? It will be permanently deleted from the system.")) return;
    
    try {
      await revokeDoctorRecord(recordId);
      setMessage("✅ Record access revoked and data purged.");
      setRecentRecords(prev => prev.filter(r => r.id !== recordId));
      fetchDashboardData(); // Refresh stats
    } catch (err: any) {
      const msg = err?.response?.data?.error || err?.message || "Revocation failed";
      setMessage(msg);
    }
  };

  const handleDecrypt = async (recordId: number) => {
    try {
      await decryptDoctorFile(recordId);
      setMessage("✅ Record decrypted and verified.");
      setInboxRecords(prev => prev.map(r => r.id === recordId ? { ...r, status: 'decrypted' } : r));
    } catch (err: any) {
      const msg = err?.response?.data?.error || err?.message || "Decryption failed";
      setMessage(msg);
    }
  };

  const safeRecords = Array.isArray(recentRecords) ? recentRecords : [];

  const stats = [
    { label: 'Total Sent', value: safeRecords.length, icon: Send, color: 'text-blue-400' },
    { label: 'Verified Patients', value: Array.from(new Set(safeRecords.map(r => r.patient))).length, icon: Users, color: 'text-emerald-400' },
    { label: 'Secure Capacity', value: '100%', icon: Shield, color: 'text-indigo-400' },
  ];

  return (
    <div className="space-y-8 animate-reveal">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-reveal delay-100">
        {stats.map((stat, i) => (
          <div key={i} className="glass-card p-6 flex items-center gap-5 hover:scale-[1.02] active:scale-[0.98]">
            <div className={`w-14 h-14 rounded-2xl bg-slate-800/50 flex items-center justify-center ${stat.color}`}>
              <stat.icon size={28} />
            </div>
            <div>
              <p className="text-xs font-bold text-slate-500 uppercase tracking-widest">{stat.label}</p>
              <p className="text-2xl font-bold text-white mt-1">{stat.value}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Tabs Navigation */}
      <div className="flex items-center gap-4 border-b border-slate-800/40 px-2 animate-reveal delay-300">
        <button
          onClick={() => setActiveTab('transfer')}
          className={`pb-4 px-4 text-xs font-bold uppercase tracking-widest transition-all relative ${
            activeTab === 'transfer' ? 'text-blue-400' : 'text-slate-500 hover:text-slate-300'
          }`}
        >
          Transfer Node
          {activeTab === 'transfer' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]"></div>}
        </button>
        <button
          onClick={() => setActiveTab('inbox')}
          className={`pb-4 px-4 text-xs font-bold uppercase tracking-widest transition-all relative ${
            activeTab === 'inbox' ? 'text-emerald-400' : 'text-slate-500 hover:text-slate-300'
          }`}
        >
          Received Records
          {activeTab === 'inbox' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]"></div>}
        </button>
        <button
          onClick={() => setActiveTab('patients')}
          className={`pb-4 px-4 text-xs font-bold uppercase tracking-widest transition-all relative ${
            activeTab === 'patients' ? 'text-purple-400' : 'text-slate-500 hover:text-slate-300'
          }`}
        >
          Network Registry
          {activeTab === 'patients' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-purple-500 shadow-[0_0_10px_rgba(168,85,247,0.5)]"></div>}
        </button>
      </div>

      {activeTab === 'inbox' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 animate-reveal delay-400">
          <div className="lg:col-span-3">
            <div className="glass-card overflow-hidden">
              <div className="p-6 border-b border-slate-800/40 flex justify-between items-center bg-slate-900/20">
                <h3 className="text-sm font-black text-white uppercase tracking-widest flex items-center gap-2">
                  <Shield className="text-emerald-400" size={16} />
                  Incoming Secure Packages
                </h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="text-[10px] font-black text-slate-500 uppercase tracking-widest border-b border-slate-800/40 bg-slate-900/40">
                      <th className="px-6 py-4">Sender</th>
                      <th className="px-6 py-4">Filename</th>
                      <th className="px-6 py-4">Timestamp</th>
                      <th className="px-6 py-4">Integrity</th>
                      <th className="px-6 py-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/40">
                    {inboxRecords.map((record) => (
                      <tr key={record.id} className="group hover:bg-emerald-500/5 transition-colors">
                        <td className="px-6 py-4">
                          <p className="text-sm font-bold text-white">{record.sender}</p>
                        </td>
                        <td className="px-6 py-4 text-sm text-slate-400 font-mono">{record.filename}</td>
                        <td className="px-6 py-4 text-xs text-slate-500">{new Date(record.created_at).toLocaleString()}</td>
                        <td className="px-6 py-4">
                          <span className={`px-2 py-1 rounded-full text-[10px] font-black uppercase tracking-tighter ${
                            record.status === 'decrypted' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                          }`}>
                            {record.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-right">
                          {record.status === 'pending' ? (
                            <button 
                              onClick={() => handleDecrypt(record.id)}
                              className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500 hover:text-white transition-all shadow-lg shadow-emerald-500/10"
                              title="Verify & Decrypt"
                            >
                              <Shield size={16} />
                            </button>
                          ) : (
                            <span className="text-emerald-500 flex items-center justify-end gap-1 text-xs font-bold">
                              <CheckCircle size={14} /> Verified
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                    {inboxRecords.length === 0 && (
                      <tr>
                        <td colSpan={5} className="px-6 py-12 text-center text-slate-500 italic text-sm">
                          No incoming medical records detected in secure buffer.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}
        {activeTab === 'transfer' && (
         <div className="grid lg:grid-cols-5 gap-8 animate-reveal delay-200">
          {/* Upload Section */}
          <div className="lg:col-span-3 space-y-6">
            <div className="glass-card p-8 md:p-10 relative overflow-hidden group">
              <div className="absolute top-0 right-0 w-32 h-32 bg-blue-600/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>
              
              <h2 className="text-2xl font-bold text-white mb-8 flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center text-blue-400">
                  <Upload size={20} />
                </div>
                Secure Transmission
              </h2>
              
              <div className="space-y-8">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-3">
                    <label className="text-xs font-bold text-slate-500 uppercase tracking-widest ml-1">Recipient Identity</label>
                    <div className="relative group">
                      <Users className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-blue-500 transition-colors" size={18} />
                      <input
                        type="email"
                        placeholder="patient@securemed.com"
                        className="w-full pl-12 pr-4 py-4 rounded-2xl bg-slate-900/40 border border-slate-800 focus:border-blue-500/50 focus:ring-4 focus:ring-blue-500/5 transition-all outline-none text-slate-200 placeholder:text-slate-600"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                      />
                    </div>
                  </div>

                  <div className="space-y-3">
                    <label className="text-xs font-bold text-slate-500 uppercase tracking-widest ml-1">Body Part / Area</label>
                    <select
                      className="w-full px-4 py-4 rounded-2xl bg-slate-900/40 border border-slate-800 focus:border-blue-500/50 focus:ring-4 focus:ring-blue-500/5 transition-all outline-none text-slate-200 appearance-none cursor-pointer"
                      value={bodyPart}
                      onChange={(e) => setBodyPart(e.target.value)}
                    >
                      {["Head", "Chest", "Abdomen", "Spine", "Limbs", "Pelvis", "Other"].map(opt => (
                        <option key={opt} value={opt} className="bg-slate-900">{opt}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-3">
                    <label className="text-xs font-bold text-slate-500 uppercase tracking-widest ml-1">Priority Level</label>
                    <div className="flex gap-2">
                      {["NORMAL", "URGENT", "EMERGENCY"].map(lvl => (
                        <button
                          key={lvl}
                          onClick={() => setPriority(lvl)}
                          className={`flex-1 py-3 rounded-xl text-[10px] font-black uppercase tracking-tighter transition-all border ${
                            priority === lvl 
                              ? lvl === 'EMERGENCY' ? 'bg-red-500/20 border-red-500 text-red-400 shadow-[0_0_15px_rgba(239,68,68,0.2)]' :
                                lvl === 'URGENT' ? 'bg-yellow-500/20 border-yellow-500 text-yellow-400 shadow-[0_0_15px_rgba(234,179,8,0.2)]' :
                                'bg-blue-500/20 border-blue-500 text-blue-400 shadow-[0_0_15px_rgba(59,130,246,0.2)]'
                              : 'bg-slate-900/40 border-slate-800 text-slate-600 hover:border-slate-700'
                          }`}
                        >
                          {lvl}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-3">
                    <label className="text-xs font-bold text-slate-500 uppercase tracking-widest ml-1">Imaging Data (DICOM)</label>
                    <div 
                      className={`relative group border-2 border-dashed rounded-[2rem] p-6 text-center transition-all cursor-pointer ${
                        file 
                          ? 'border-blue-500/50 bg-blue-500/5' 
                          : 'border-slate-800 hover:border-slate-700 bg-slate-900/20'
                      }`}
                      onDragOver={(e) => e.preventDefault()}
                      onDrop={(e) => {
                        e.preventDefault();
                        setFile(e.dataTransfer.files[0] || null);
                      }}
                      onClick={() => fileInputRef.current?.click()}
                    >
                      <input
                        ref={fileInputRef}
                        type="file"
                        className="hidden"
                        onChange={(e) => setFile(e.target.files?.[0] || null)}
                        accept=".dcm"
                      />
                      
                      {file ? (
                        <div className="flex items-center gap-4 animate-in zoom-in duration-300">
                          <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center text-blue-400 shrink-0">
                            <FileDigit size={24} />
                          </div>
                          <div className="text-left min-w-0">
                            <span className="text-blue-400 font-bold text-sm truncate block">{file.name}</span>
                            <span className="text-slate-600 text-[10px] uppercase font-black">{(file.size / 1024 / 1024).toFixed(2)} MB</span>
                          </div>
                          <button 
                            onClick={(e) => { e.stopPropagation(); setFile(null); }}
                            className="ml-auto text-slate-500 hover:text-red-400 transition-colors"
                          >
                            <X size={16} />
                          </button>
                        </div>
                      ) : (
                        <div className="flex items-center gap-4 group-hover:translate-x-1 transition-transform">
                          <div className="w-12 h-12 rounded-xl bg-slate-800/40 flex items-center justify-center text-slate-600">
                            <FileUp size={24} />
                          </div>
                          <div className="text-left">
                            <span className="text-slate-400 font-bold text-sm">Select DICOM</span>
                            <p className="text-[10px] text-slate-600 uppercase font-black">Ready for encryption</p>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                <div className="space-y-3">
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-widest ml-1">Clinical Observations & Notes</label>
                  <textarea
                    placeholder="Enter clinical notes, findings, or instructions for the patient..."
                    className="w-full px-6 py-4 rounded-2xl bg-slate-900/40 border border-slate-800 focus:border-blue-500/50 focus:ring-4 focus:ring-blue-500/5 transition-all outline-none text-slate-200 placeholder:text-slate-700 h-32 resize-none"
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                  />
                </div>

                <div className="pt-4">
                  <button
                    onClick={handleSend}
                    disabled={loading}
                    className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold py-5 rounded-[1.5rem] shadow-2xl shadow-blue-500/20 transition-all transform active:scale-[0.98] disabled:opacity-50 flex justify-center items-center gap-3 group"
                  >
                    {loading ? (
                      <div className="w-6 h-6 border-3 border-white/20 border-t-white rounded-full animate-spin"></div>
                    ) : (
                      <>
                        <span>Securely Encrypt & Send</span>
                        <Shield size={20} className="group-hover:scale-110 transition-transform" />
                      </>
                    )}
                  </button>

                  {message && (
                    <div className={`mt-6 p-4 rounded-2xl text-sm font-bold text-center border animate-in slide-in-from-top-2 duration-300 ${
                      message.includes('✅') 
                        ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' 
                        : 'bg-yellow-500/10 border-yellow-500/20 text-yellow-400'
                    }`}>
                      {message}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Recent Activity Section */}
          <div className="lg:col-span-2">
            <div className="glass-card p-8 h-full flex flex-col">
              <div className="flex items-center justify-between mb-8">
                <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center text-indigo-400">
                    <History size={20} />
                  </div>
                  History
                </h2>
                <button 
                  onClick={fetchDashboardData}
                  className="p-2 text-slate-500 hover:text-white transition-colors"
                  title="Refresh History"
                >
                  <History size={16} />
                </button>
              </div>
              
              <div className="flex-1 space-y-4 overflow-y-auto pr-2 custom-scrollbar">
                {fetchingRecords ? (
                  <div className="space-y-4">
                    {[1, 2, 3, 4].map(i => (
                      <div key={i} className="h-24 bg-slate-900/40 animate-pulse rounded-2xl border border-slate-800/40"></div>
                    ))}
                  </div>
                ) : safeRecords.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full opacity-30 py-20">
                    <FileText size={48} className="mb-4" />
                    <p className="font-bold uppercase tracking-widest text-xs">No records found</p>
                  </div>
                ) : (
                  safeRecords.map((record) => (
                    <div key={record.id} className="p-5 rounded-2xl bg-slate-900/40 border border-slate-800/40 hover:border-blue-500/30 transition-all group">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex items-center gap-4 min-w-0">
                          <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center text-slate-500 shrink-0 group-hover:bg-blue-500/10 group-hover:text-blue-400 transition-colors">
                            <FileDigit size={20} />
                          </div>
                          <div className="min-w-0">
                            <p className="font-bold text-slate-200 truncate group-hover:text-white transition-colors">{record.filename}</p>
                            <p className="text-xs text-slate-500 truncate mt-0.5">Recipient: {record.patient}</p>
                          </div>
                        </div>
                        <div className={`px-3 py-1 rounded-full text-[10px] font-extrabold uppercase tracking-widest flex items-center gap-1.5 shrink-0 ${
                          record.priority === 'EMERGENCY' ? 'bg-red-500/10 text-red-400 border border-red-500/20' :
                          record.priority === 'URGENT' ? 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20' :
                          'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        }`}>
                          {record.priority === 'EMERGENCY' ? <AlertCircle size={10} /> : <CheckCircle size={10} />}
                          {record.priority}
                        </div>
                      </div>
                      <div className="flex items-center justify-between mt-4 pt-4 border-t border-slate-800/40">
                        <div className="flex items-center gap-3">
                          <p className="text-[10px] text-slate-600 font-bold uppercase tracking-tighter">
                            {record.body_part}
                          </p>
                          <span className="text-slate-800">•</span>
                          <p className="text-[10px] text-slate-600 font-bold uppercase tracking-tighter">
                            {new Date(record.created_at).toLocaleDateString()}
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <button 
                            onClick={() => setSelectedRecord(record)}
                            className="text-[10px] font-bold text-blue-500 uppercase tracking-widest hover:text-blue-400 transition-colors"
                          >
                            View Details
                          </button>
                          <button 
                            onClick={() => handleRevoke(record.id)}
                            className="p-1.5 rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-500/10 transition-all"
                            title="Revoke Record"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'patients' && (
        /* Patient Directory */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-reveal delay-200">
          {patients.map((patient, idx) => (
            <div key={idx} className="glass-card p-6 group hover:border-blue-500/30 transition-all">
              <div className="flex items-center gap-4 mb-6">
                <div className="w-14 h-14 rounded-2xl bg-slate-800 flex items-center justify-center text-slate-400 group-hover:bg-blue-500/10 group-hover:text-blue-400 transition-colors">
                  <User size={28} />
                </div>
                <div className="min-w-0">
                  <h3 className="font-bold text-white truncate">{patient.email.split('@')[0]}</h3>
                  <p className="text-[10px] text-slate-500 uppercase tracking-widest font-black truncate">{patient.email}</p>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4 py-4 border-y border-slate-800/40 mb-6">
                <div>
                  <p className="text-[10px] text-slate-500 uppercase font-bold tracking-tighter">Total Records</p>
                  <p className="text-xl font-black text-slate-200">{patient.total_records}</p>
                </div>
                <div>
                  <p className="text-[10px] text-slate-500 uppercase font-bold tracking-tighter">Network Status</p>
                  <div className="flex items-center gap-1.5 mt-1">
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div>
                    <span className="text-xs font-bold text-emerald-500 uppercase tracking-widest">{patient.status}</span>
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                <p className="text-[10px] text-slate-600 font-black uppercase tracking-widest flex items-center gap-2">
                  <Clock size={12} />
                  Last Interaction: {new Date(patient.last_interaction).toLocaleDateString()}
                </p>
                <button 
                  onClick={() => setSelectedPatient(patient)}
                  className="w-full py-3 rounded-xl bg-slate-900 border border-slate-800 text-xs font-bold text-slate-400 group-hover:text-blue-400 group-hover:border-blue-500/30 transition-all flex items-center justify-center gap-2"
                >
                  Patient Details
                  <ArrowRight size={14} />
                </button>
              </div>
            </div>
          ))}
          {patients.length === 0 && (
            <div className="col-span-full py-32 glass-card border-dashed flex flex-col items-center opacity-30">
              <Users size={48} className="mb-4" />
              <p className="font-black uppercase tracking-[0.2em] text-xs">Patient Directory Empty</p>
            </div>
          )}
        </div>
      )}

      {/* Record Details Modal */}
      {selectedRecord && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-300">
          <div className="glass-card w-full max-w-2xl overflow-hidden flex flex-col animate-in zoom-in-95 duration-300">
            <div className="p-6 border-b border-slate-800/60 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center text-blue-400">
                  <FileText size={20} />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white tracking-tight">Record Details</h3>
                  <p className="text-[10px] text-slate-500 font-black uppercase tracking-widest">{selectedRecord.filename}</p>
                </div>
              </div>
              <button 
                onClick={() => setSelectedRecord(null)}
                className="p-2 rounded-lg hover:bg-slate-800 text-slate-500 hover:text-white transition-colors"
              >
                <X size={20} />
              </button>
            </div>
            <div className="p-8 space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <div className="p-4 rounded-2xl bg-slate-900/40 border border-slate-800">
                  <p className="text-[10px] font-bold text-slate-600 uppercase mb-1">Recipient</p>
                  <p className="text-sm font-bold text-slate-200">{selectedRecord.patient}</p>
                </div>
                <div className="p-4 rounded-2xl bg-slate-900/40 border border-slate-800">
                  <p className="text-[10px] font-bold text-slate-600 uppercase mb-1">Transmitted</p>
                  <p className="text-sm font-bold text-slate-200">{new Date(selectedRecord.created_at).toLocaleString()}</p>
                </div>
                <div className="p-4 rounded-2xl bg-slate-900/40 border border-slate-800">
                  <p className="text-[10px] font-bold text-slate-600 uppercase mb-1">Modality</p>
                  <p className="text-sm font-bold text-slate-200">{selectedRecord.body_part} / DICOM</p>
                </div>
                <div className="p-4 rounded-2xl bg-slate-900/40 border border-slate-800">
                  <p className="text-[10px] font-bold text-slate-600 uppercase mb-1">Priority</p>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-widest ${
                    selectedRecord.priority === 'EMERGENCY' ? 'bg-red-500/20 text-red-400' :
                    selectedRecord.priority === 'URGENT' ? 'bg-yellow-500/20 text-yellow-400' :
                    'bg-emerald-500/20 text-emerald-400'
                  }`}>
                    {selectedRecord.priority}
                  </span>
                </div>
              </div>
            </div>
            <div className="p-6 border-t border-slate-800/60 bg-slate-900/20 flex justify-end">
              <button 
                onClick={() => setSelectedRecord(null)}
                className="px-6 py-2 rounded-xl bg-blue-600 text-xs font-bold text-white hover:bg-blue-500 transition-all"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Patient Details Modal */}
      {selectedPatient && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-300">
          <div className="glass-card w-full max-w-2xl overflow-hidden flex flex-col animate-in zoom-in-95 duration-300">
            <div className="p-6 border-b border-slate-800/60 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center text-blue-400">
                  <User size={20} />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white tracking-tight">Patient Profile</h3>
                  <p className="text-[10px] text-slate-500 font-black uppercase tracking-widest">{selectedPatient.email}</p>
                </div>
              </div>
              <button 
                onClick={() => setSelectedPatient(null)}
                className="p-2 rounded-lg hover:bg-slate-800 text-slate-500 hover:text-white transition-colors"
              >
                <X size={20} />
              </button>
            </div>
            <div className="p-8 space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <div className="p-4 rounded-2xl bg-slate-900/40 border border-slate-800">
                  <p className="text-[10px] font-bold text-slate-600 uppercase mb-1">Total Records Shared</p>
                  <p className="text-xl font-bold text-slate-200">{selectedPatient.total_records}</p>
                </div>
                <div className="p-4 rounded-2xl bg-slate-900/40 border border-slate-800">
                  <p className="text-[10px] font-bold text-slate-600 uppercase mb-1">Network Status</p>
                  <div className="flex items-center gap-1.5 mt-1">
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div>
                    <span className="text-xs font-bold text-emerald-500 uppercase tracking-widest">{selectedPatient.status}</span>
                  </div>
                </div>
                <div className="col-span-2 p-4 rounded-2xl bg-slate-900/40 border border-slate-800">
                  <p className="text-[10px] font-bold text-slate-600 uppercase mb-1">Last Interaction</p>
                  <p className="text-sm font-bold text-slate-200">{new Date(selectedPatient.last_interaction).toLocaleString()}</p>
                </div>
              </div>
            </div>
            <div className="p-6 border-t border-slate-800/60 bg-slate-900/20 flex justify-end">
              <button 
                onClick={() => setSelectedPatient(null)}
                className="px-6 py-2 rounded-xl bg-blue-600 text-xs font-bold text-white hover:bg-blue-500 transition-all"
              >
                Close Profile
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
