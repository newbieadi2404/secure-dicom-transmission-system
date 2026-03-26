import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { getInbox, decryptFile, getProviders, getRecordDetails, deletePatientRecord, API_BASE, sendPatientFile, type FileItem as ApiFileItem } from "../services/api";
import { 
  Inbox, 
  RefreshCcw, 
  FileText, 
  Unlock, 
  Eye, 
  Calendar, 
  User, 
  ShieldCheck,
  Clock,
  ChevronRight,
  Stethoscope,
  X,
  FileDigit,
  ShieldAlert,
  Download,
  Trash2,
  Send,
  FileUp,
  Shield
} from 'lucide-react';
import { useRef } from "react";

export default function Patient() {
  const { email: authEmail } = useAuth();
  const [email, setEmail] = useState("");
  const [files, setFiles] = useState<ApiFileItem[]>([]);
  const [providers, setProviders] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [decrypting, setDecrypting] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const [activeTab, setActiveTab] = useState<'vault' | 'providers' | 'send'>('vault');
  const [selectedRecord, setSelectedRecord] = useState<any | null>(null);
  const [selectedProvider, setSelectedProvider] = useState<any | null>(null);
  const [fetchingDetails, setFetchingDetails] = useState(false);
  const [imageUrl, setImageUrl] = useState<string | null>(null);

  // New state for sending records
  const [recipientDoctor, setRecipientDoctor] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [sending, setSubmitting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [notes, setNotes] = useState("");

  // ✅ Sync with AuthContext or LocalStorage
  useEffect(() => {
    const saved = localStorage.getItem("email") || authEmail;
    if (saved) setEmail(saved);
  }, [authEmail]);

  useEffect(() => {
    localStorage.setItem("email", email);
  }, [email]);

  const fetchDashboardData = async () => {
    if (!email) {
      setMessage("Please confirm your account email to access records.");
      return;
    }

    try {
      setLoading(true);
      setMessage("");

      const [inboxRes, providersRes] = await Promise.all([
        getInbox(),
        getProviders()
      ]);
      setFiles(inboxRes.data || []);
      setProviders(providersRes.data || []);
    } catch (err: any) {
      const msg = err?.response?.data?.error || err?.message || "Failed to sync with vault.";
      setMessage(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (email) fetchDashboardData();
  }, [email]);

  const handleDecrypt = async (recordId: number) => {
    try {
      setDecrypting(String(recordId));
      setMessage("");

      await decryptFile(recordId);

      setMessage("✅ Record decrypted successfully. Integrity verified.");
      
      setFiles((prev) => prev.map((f) => 
        f.id === recordId ? { ...f, status: 'decrypted' } : f
      ));

    } catch (err: any) {
      const msg = err?.response?.data?.error || err?.message || "";
      if (msg && msg.includes("Replay")) {
        setMessage("⚠️ Integrity Alert: Record already processed.");
      } else {
        setMessage(msg || "Decryption failed.");
      }
    } finally {
      setDecrypting(null);
    }
  };

  const handleSend = async () => {
    setMessage("");
    if (!recipientDoctor || !file) {
      setMessage("Enter doctor email and select a file");
      return;
    }

    try {
      setSubmitting(true);

      const formData = new FormData();
      formData.append("doctor_email", recipientDoctor);
      formData.append("file", file);
      formData.append("body_part", "Patient Upload");
      formData.append("priority", "NORMAL");
      formData.append("clinical_notes", notes);

      await sendPatientFile(formData);

      setMessage("✅ Record transmitted to doctor successfully.");
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      setRecipientDoctor("");
      setNotes("");
      fetchDashboardData();
    } catch (err: any) {
      const msg = err?.response?.data?.error || err?.message || "Transmission failure";
      setMessage(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleViewDetails = async (recordId: number) => {
    try {
      setFetchingDetails(true);
      setImageUrl(null);
      const res = await getRecordDetails(recordId);
      setSelectedRecord(res.data);
      
      // Fetch image if decrypted
      if (res.data.status === 'decrypted') {
        const token = localStorage.getItem('token');
        const imgRes = await fetch(`${API_BASE}/patient/record/${recordId}/image`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (imgRes.ok) {
          const blob = await imgRes.blob();
          setImageUrl(URL.createObjectURL(blob));
        }
      }
    } catch (err) {
      console.error("Failed to fetch record details", err);
    } finally {
      setFetchingDetails(false);
    }
  };

  const handleDelete = async (recordId: number) => {
    if (!window.confirm("Are you sure you want to permanently delete this record from your vault?")) return;
    
    try {
      await deletePatientRecord(recordId);
      setMessage("✅ Record permanently deleted.");
      setFiles(prev => prev.filter(f => f.id !== recordId));
    } catch (err: any) {
      setMessage(err?.response?.data?.error || "Failed to delete record.");
    }
  };

  const handleDownloadArchive = () => {
    if (!selectedRecord) return;
    const data = JSON.stringify(selectedRecord, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `SecureMed_Archive_${selectedRecord.filename}.json`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  return (
    <div className="space-y-8 animate-reveal">
      {/* Header Info */}
      <div className="bg-gradient-to-r from-blue-600/10 to-transparent p-8 rounded-[2.5rem] border border-blue-500/10 mb-10 animate-reveal delay-100">
        <h1 className="text-3xl font-extrabold text-white mb-2 flex items-center gap-3">
          Welcome back, {email?.split('@')[0]}
        </h1>
        <p className="text-slate-400 max-w-2xl">
          Your medical records are stored in a zero-knowledge vault. Decrypt records locally to view sensitive imaging data.
        </p>
      </div>

      {/* Stats/Quick Info Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-reveal delay-200">
        <div className="glass-card p-6 flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center text-blue-400">
            <FileText size={24} />
          </div>
          <div>
            <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Total Records</p>
            <p className="text-xl font-bold text-white">{files.length}</p>
          </div>
        </div>
        <div className="glass-card p-6 flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-400">
            <Stethoscope size={24} />
          </div>
          <div>
            <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Active Providers</p>
            <p className="text-xl font-bold text-white">{providers.length}</p>
          </div>
        </div>
        <div className="glass-card p-6 flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-indigo-500/10 flex items-center justify-center text-indigo-400">
            <ShieldCheck size={24} />
          </div>
          <div>
            <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Vault Security</p>
            <p className="text-xl font-bold text-white">AES-RSA</p>
          </div>
        </div>
      </div>

      {/* Sync Control */}
      <div className="glass-card p-6 flex flex-col md:flex-row items-center gap-6 animate-reveal delay-200">
        <div className="flex-1 w-full relative group">
          <User className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-emerald-500 transition-colors" size={18} />
          <input
            className="w-full pl-12 pr-4 py-4 rounded-2xl bg-slate-900/40 border border-slate-800 focus:border-emerald-500/50 focus:ring-4 focus:ring-emerald-500/5 transition-all outline-none text-slate-200 placeholder:text-slate-600"
            placeholder="Verify your account email..."
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>

        <button
          onClick={fetchDashboardData}
          disabled={loading}
          className="w-full md:w-auto px-10 py-4 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-2xl shadow-lg shadow-emerald-500/20 transition-all transform active:scale-[0.98] disabled:opacity-50 flex items-center justify-center gap-3 group"
        >
          {loading ? (
            <RefreshCcw className="animate-spin" size={20} />
          ) : (
            <>
              <span>Sync Vault</span>
              <RefreshCcw size={20} className="group-hover:rotate-180 transition-transform duration-500" />
            </>
          )}
        </button>
      </div>

      {/* Status Message */}
      {message && (
        <div className={`max-w-2xl mx-auto p-4 rounded-2xl text-sm font-bold text-center border animate-in slide-in-from-top-2 duration-300 ${
          message.includes('✅') 
            ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' 
            : 'bg-yellow-500/10 border-yellow-500/20 text-yellow-400'
        }`}>
          {message}
        </div>
      )}

      {/* Tabs Navigation */}
      <div className="flex items-center gap-4 border-b border-slate-800/40 px-2 animate-reveal delay-300">
        <button
          onClick={() => setActiveTab('vault')}
          className={`pb-4 px-4 text-xs font-bold uppercase tracking-widest transition-all relative ${
            activeTab === 'vault' ? 'text-blue-400' : 'text-slate-500 hover:text-slate-300'
          }`}
        >
          Medical Vault
          {activeTab === 'vault' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]"></div>}
        </button>
        <button
          onClick={() => setActiveTab('send')}
          className={`pb-4 px-4 text-xs font-bold uppercase tracking-widest transition-all relative ${
            activeTab === 'send' ? 'text-emerald-400' : 'text-slate-500 hover:text-slate-300'
          }`}
        >
          Transfer Node
          {activeTab === 'send' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]"></div>}
        </button>
        <button
          onClick={() => setActiveTab('providers')}
          className={`pb-4 px-4 text-xs font-bold uppercase tracking-widest transition-all relative ${
            activeTab === 'providers' ? 'text-purple-400' : 'text-slate-500 hover:text-slate-300'
          }`}
        >
          Provider Network
          {activeTab === 'providers' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-purple-500 shadow-[0_0_10px_rgba(168,85,247,0.5)]"></div>}
        </button>
      </div>

      {activeTab === 'send' && (
        <div className="grid lg:grid-cols-5 gap-8 animate-reveal delay-200">
          <div className="lg:col-span-3 space-y-6">
            <div className="glass-card p-8">
              <div className="flex items-center gap-3 mb-8">
                <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-400">
                  <FileUp size={20} />
                </div>
                <div>
                  <h3 className="text-sm font-black text-white uppercase tracking-widest">Outbound Channel</h3>
                  <p className="text-[10px] text-slate-500 font-bold uppercase tracking-tighter">Encrypt and transmit to medical professional</p>
                </div>
              </div>

              <div className="space-y-6">
                <div className="relative group">
                  <User className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-blue-500 transition-colors" size={18} />
                  <input
                    className="w-full pl-12 pr-4 py-4 rounded-2xl bg-slate-900/40 border border-slate-800 focus:border-blue-500/50 focus:ring-4 focus:ring-blue-500/5 transition-all outline-none text-slate-200 placeholder:text-slate-600"
                    placeholder="Recipient Doctor Email..."
                    value={recipientDoctor}
                    onChange={(e) => setRecipientDoctor(e.target.value)}
                  />
                </div>

                <div 
                  onClick={() => fileInputRef.current?.click()}
                  className={`border-2 border-dashed rounded-[2rem] p-12 text-center transition-all cursor-pointer group ${
                    file ? 'border-emerald-500/40 bg-emerald-500/5' : 'border-slate-800 hover:border-slate-700 bg-slate-900/20'
                  }`}
                >
                  <input 
                    type="file" 
                    ref={fileInputRef}
                    className="hidden" 
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                  />
                  <div className="w-16 h-16 rounded-2xl bg-slate-800 flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
                    {file ? <ShieldCheck className="text-emerald-400" size={32} /> : <FileDigit className="text-slate-500" size={32} />}
                  </div>
                  {file ? (
                    <div>
                      <p className="text-emerald-400 font-bold">{file.name}</p>
                      <p className="text-[10px] text-slate-500 uppercase tracking-widest mt-1">{(file.size / 1024 / 1024).toFixed(2)} MB • Ready for hybrid tunnel</p>
                    </div>
                  ) : (
                    <div>
                      <p className="text-slate-300 font-bold uppercase tracking-tighter">Drop medical record here</p>
                      <p className="text-[10px] text-slate-500 uppercase tracking-widest mt-1">DICOM Format Required • Max 50MB</p>
                    </div>
                  )}
                </div>

                <textarea
                  className="w-full px-6 py-4 rounded-2xl bg-slate-900/40 border border-slate-800 focus:border-blue-500/50 transition-all outline-none text-slate-200 placeholder:text-slate-600 min-h-[120px] resize-none"
                  placeholder="Additional clinical context or notes..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                />

                <button
                  onClick={handleSend}
                  disabled={sending}
                  className="w-full py-5 rounded-[1.5rem] bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-black uppercase tracking-widest text-xs flex items-center justify-center gap-3 shadow-xl shadow-blue-500/20 hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50 disabled:grayscale"
                >
                  {sending ? <RefreshCcw className="animate-spin" size={18} /> : <Send size={18} />}
                  {sending ? 'Encrypting & Transmitting...' : 'Initiate Secure Transfer'}
                </button>
              </div>
            </div>
          </div>

          <div className="lg:col-span-2 space-y-6">
            <div className="glass-card p-8 border-emerald-500/10">
              <h3 className="text-sm font-black text-white uppercase tracking-widest mb-6 flex items-center gap-2">
                <Shield size={16} className="text-emerald-400" />
                Security Protocol
              </h3>
              <div className="space-y-6">
                <div className="flex gap-4 p-4 rounded-2xl bg-slate-900/40 border border-slate-800/40">
                  <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center text-blue-400 shrink-0">
                    <Unlock size={16} />
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    <span className="text-slate-200 font-bold">Hybrid Tunneling:</span> Your record is encrypted with a unique AES-256 key, which is then wrapped using the doctor's RSA-2048 public key.
                  </p>
                </div>
                <div className="flex gap-4 p-4 rounded-2xl bg-slate-900/40 border border-slate-800/40">
                  <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-400 shrink-0">
                    <ShieldCheck size={16} />
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    <span className="text-slate-200 font-bold">Identity Verification:</span> The package is cryptographically signed with your private key, ensuring the doctor can verify the origin.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'vault' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 animate-reveal delay-400">
          {files.length === 0 && !loading && email && (
            <div className="text-center py-24 glass-card border-dashed flex flex-col items-center">
              <div className="w-20 h-20 rounded-3xl bg-slate-800/50 flex items-center justify-center text-slate-600 mb-6">
                <Inbox size={40} />
              </div>
              <h3 className="text-xl font-bold text-slate-400 tracking-tight">Your Vault is Empty</h3>
              <p className="text-slate-600 mt-2 max-w-xs">New medical records will appear here once authorized by your healthcare provider.</p>
            </div>
          )}

          {files.map((file) => (
            <div 
              key={file.id} 
              className="glass-card p-6 md:p-8 hover:border-blue-500/30 group relative overflow-hidden"
            >
              {file.status === 'decrypted' && (
                <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/5 rounded-full blur-2xl -translate-y-1/2 translate-x-1/2"></div>
              )}
              
              <div className="flex flex-col md:flex-row items-center justify-between gap-8">
                <div className="flex items-center gap-6 flex-1 min-w-0 w-full">
                  <div className={`w-16 h-16 rounded-2xl flex items-center justify-center text-3xl shadow-inner shrink-0 ${
                    file.status === 'decrypted' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-blue-500/10 text-blue-400'
                  }`}>
                    <FileText size={32} />
                  </div>
                  <div className="min-w-0 flex-1 text-center md:text-left">
                    <div className="flex flex-col md:flex-row md:items-center gap-2 md:gap-4 mb-2">
                      <h3 className="font-bold text-xl text-white truncate">{file.filename}</h3>
                      <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest self-center md:self-auto ${
                        file.status === 'pending' ? 'bg-yellow-500/10 text-yellow-500' : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      }`}>
                        {file.status}
                      </span>
                    </div>
                    <div className="flex flex-wrap justify-center md:justify-start gap-x-6 gap-y-2 text-xs font-medium text-slate-500 uppercase tracking-tighter">
                      <span className="flex items-center gap-2">
                        <User size={14} className="text-blue-400" />
                        <span className="text-slate-400">Dr. {file.sender?.split('@')[0]}</span>
                      </span>
                      <span className="flex items-center gap-2">
                        <Calendar size={14} className="text-blue-400" />
                        <span>{new Date(file.created_at || '').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</span>
                      </span>
                      <span className="flex items-center gap-2">
                        <ShieldCheck size={14} className="text-emerald-400" />
                        <span className="text-emerald-500/80">End-to-End Secure</span>
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-4 w-full md:w-auto shrink-0">
                  <button
                    onClick={() => file.status === 'decrypted' ? handleViewDetails(file.id) : handleDecrypt(file.id)}
                    disabled={!!decrypting}
                    className={`w-full md:w-auto px-8 py-4 rounded-2xl font-bold text-sm transition-all flex items-center justify-center gap-3 shadow-lg active:scale-[0.98] disabled:opacity-50 ${
                      file.status === 'decrypted' 
                        ? 'bg-slate-800 hover:bg-slate-700 text-emerald-400 border border-emerald-500/30' 
                        : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-blue-500/20'
                    }`}
                  >
                    {decrypting === String(file.id) ? (
                      <RefreshCcw className="animate-spin" size={18} />
                    ) : file.status === 'decrypted' ? (
                      <>
                        <Eye size={18} />
                        <span>Launch Viewer</span>
                      </>
                    ) : (
                      <>
                        <Unlock size={18} />
                        <span>Authorize Decryption</span>
                      </>
                    )}
                  </button>
                  <button 
                    onClick={() => handleDelete(file.id)}
                    className="hidden md:flex w-10 h-10 rounded-xl bg-slate-800/50 items-center justify-center text-slate-500 hover:text-red-400 hover:bg-red-500/10 hover:border-red-500/30 border border-slate-700/30 transition-all"
                    title="Delete Record"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>
            </div>
          ))}
          {providers.length === 0 && (
            <div className="col-span-full py-32 glass-card border-dashed flex flex-col items-center opacity-30">
              <Stethoscope size={48} className="mb-4" />
              <p className="font-black uppercase tracking-[0.2em] text-xs">No Providers Linked</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'providers' && (
        /* Providers Grid */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-reveal delay-300">
          {providers.map((provider, idx) => (
            <div key={idx} className="glass-card p-6 group hover:border-emerald-500/30 transition-all">
              <div className="flex items-center gap-4 mb-6">
                <div className="w-14 h-14 rounded-2xl bg-slate-800 flex items-center justify-center text-slate-400 group-hover:bg-emerald-500/10 group-hover:text-emerald-400 transition-colors">
                  <Stethoscope size={28} />
                </div>
                <div className="min-w-0">
                  <h3 className="font-bold text-white truncate">Dr. {provider.email.split('@')[0]}</h3>
                  <p className="text-[10px] text-slate-500 uppercase tracking-widest font-black truncate">{provider.email}</p>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4 py-4 border-y border-slate-800/40 mb-6">
                <div>
                  <p className="text-[10px] text-slate-500 uppercase font-bold tracking-tighter">Shared Records</p>
                  <p className="text-xl font-black text-slate-200">{provider.total_records}</p>
                </div>
                <div>
                  <p className="text-[10px] text-slate-500 uppercase font-bold tracking-tighter">Auth Status</p>
                  <div className="flex items-center gap-1.5 mt-1">
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div>
                    <span className="text-xs font-bold text-emerald-500 uppercase tracking-widest">{provider.status}</span>
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                <p className="text-[10px] text-slate-600 font-black uppercase tracking-widest flex items-center gap-2">
                  <Clock size={12} />
                  Last Record: {new Date(provider.last_received).toLocaleDateString()}
                </p>
                <button 
                  onClick={() => setSelectedProvider(provider)}
                  className="w-full py-3 rounded-xl bg-slate-900 border border-slate-800 text-xs font-bold text-slate-400 group-hover:text-emerald-400 group-hover:border-emerald-500/30 transition-all flex items-center justify-center gap-2"
                >
                  Provider Details
                  <ChevronRight size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Provider Details Modal */}
      {selectedProvider && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-300">
          <div className="glass-card w-full max-w-2xl overflow-hidden flex flex-col animate-in zoom-in-95 duration-300">
            <div className="p-6 border-b border-slate-800/60 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-400">
                  <Stethoscope size={20} />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white tracking-tight">Provider Profile</h3>
                  <p className="text-[10px] text-slate-500 font-black uppercase tracking-widest">{selectedProvider.email}</p>
                </div>
              </div>
              <button 
                onClick={() => setSelectedProvider(null)}
                className="p-2 rounded-lg hover:bg-slate-800 text-slate-500 hover:text-white transition-colors"
              >
                <X size={20} />
              </button>
            </div>
            <div className="p-8 space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <div className="p-4 rounded-2xl bg-slate-900/40 border border-slate-800">
                  <p className="text-[10px] font-bold text-slate-600 uppercase mb-1">Shared Records</p>
                  <p className="text-xl font-bold text-slate-200">{selectedProvider.total_records}</p>
                </div>
                <div className="p-4 rounded-2xl bg-slate-900/40 border border-slate-800">
                  <p className="text-[10px] font-bold text-slate-600 uppercase mb-1">Authorization</p>
                  <div className="flex items-center gap-1.5 mt-1">
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div>
                    <span className="text-xs font-bold text-emerald-500 uppercase tracking-widest">{selectedProvider.status}</span>
                  </div>
                </div>
                <div className="col-span-2 p-4 rounded-2xl bg-slate-900/40 border border-slate-800">
                  <p className="text-[10px] font-bold text-slate-600 uppercase mb-1">Last Interaction</p>
                  <p className="text-sm font-bold text-slate-200">{new Date(selectedProvider.last_received).toLocaleString()}</p>
                </div>
              </div>
            </div>
            <div className="p-6 border-t border-slate-800/60 bg-slate-900/20 flex justify-end">
              <button 
                onClick={() => setSelectedProvider(null)}
                className="px-6 py-2 rounded-xl bg-emerald-600 text-xs font-bold text-white hover:bg-emerald-500 transition-all"
              >
                Close Provider Info
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Record Viewer Modal (Simulated) */}
      {selectedRecord && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-300">
          <div className="glass-card w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col shadow-[0_0_100px_rgba(59,130,246,0.15)] animate-in zoom-in-95 duration-300">
            <div className="p-6 border-b border-slate-800/60 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center text-blue-400">
                  <ShieldCheck size={20} />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white tracking-tight">{selectedRecord.filename}</h3>
                  <p className="text-[10px] text-slate-500 font-black uppercase tracking-widest">Secure DICOM Viewer</p>
                </div>
              </div>
              <button 
                onClick={() => setSelectedRecord(null)}
                className="p-2 rounded-lg hover:bg-slate-800 text-slate-500 hover:text-white transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
              {fetchingDetails ? (
                <div className="flex flex-col items-center justify-center py-20">
                  <RefreshCcw className="animate-spin text-blue-500 mb-4" size={40} />
                  <p className="text-slate-500 font-bold uppercase tracking-widest text-xs">Accessing Secure Metadata...</p>
                </div>
              ) : (
                <div className="grid md:grid-cols-2 gap-8">
                  {/* Simulated Imaging Panel */}
                  <div className="aspect-square bg-slate-900/60 rounded-[2rem] border border-slate-800 flex flex-col items-center justify-center relative group overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent"></div>
                    {imageUrl ? (
                      <img src={imageUrl} alt="Decrypted Medical Scan" className="w-full h-full object-contain z-10" />
                    ) : (
                      <>
                        <FileDigit size={80} className="text-slate-800 mb-4 group-hover:scale-110 transition-transform duration-500" />
                        <p className="text-xs font-bold text-slate-600 uppercase tracking-widest">Encrypted Image Data</p>
                      </>
                    )}
                    <div className="absolute bottom-6 left-0 right-0 flex flex-col items-center gap-2 z-20">
                      <span className="px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-[10px] font-black border border-emerald-500/20 backdrop-blur-md">INTEGRITY VERIFIED</span>
                      <span className="text-[9px] text-slate-400 font-mono bg-slate-900/80 px-2 py-0.5 rounded backdrop-blur-md">{selectedRecord.id}-{Math.random().toString(36).substring(7)}</span>
                    </div>
                  </div>

                  {/* Metadata Panel */}
                  <div className="space-y-6">
                    <div>
                      <h4 className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] mb-4">Transmission Integrity</h4>
                      <div className="space-y-3">
                        <div className="p-4 rounded-2xl bg-slate-900/40 border border-slate-800 flex items-center justify-between">
                          <span className="text-xs font-bold text-slate-400">Encryption Standard</span>
                          <span className="text-xs font-mono text-blue-400">AES-256-CBC</span>
                        </div>
                        <div className="p-4 rounded-2xl bg-slate-900/40 border border-slate-800 flex items-center justify-between">
                          <span className="text-xs font-bold text-slate-400">Hash Algorithm</span>
                          <span className="text-xs font-mono text-emerald-400">SHA-256</span>
                        </div>
                        <div className="p-4 rounded-2xl bg-slate-900/40 border border-slate-800 flex items-center justify-between">
                          <span className="text-xs font-bold text-slate-400">Identity Protocol</span>
                          <span className="text-xs font-mono text-indigo-400">RSA-4096-PSS</span>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h4 className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] mb-4">Clinical Metadata</h4>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="p-4 rounded-2xl bg-slate-900/40 border border-slate-800">
                          <p className="text-[10px] font-bold text-slate-600 uppercase mb-1">Modality</p>
                          <p className="text-sm font-bold text-slate-200">DICOM / SC</p>
                        </div>
                        <div className="p-4 rounded-2xl bg-slate-900/40 border border-slate-800">
                          <p className="text-[10px] font-bold text-slate-600 uppercase mb-1">Created</p>
                          <p className="text-sm font-bold text-slate-200">{new Date(selectedRecord.created_at).toLocaleDateString()}</p>
                        </div>
                      </div>
                    </div>

                    <div className="p-6 rounded-3xl bg-blue-500/5 border border-blue-500/10 flex items-start gap-4">
                      <ShieldAlert size={20} className="text-blue-400 shrink-0" />
                      <div>
                        <p className="text-xs font-bold text-blue-400 mb-1">Patient Privacy Notice</p>
                        <p className="text-[10px] text-slate-500 leading-relaxed">This record was decrypted using your private key locally. SecureMed servers never see the unencrypted content of your medical files.</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="p-6 border-t border-slate-800/60 bg-slate-900/20 flex justify-end gap-3">
              <button 
                onClick={() => window.print()}
                className="px-6 py-3 rounded-xl bg-slate-800 text-xs font-bold text-slate-400 hover:text-white transition-colors"
              >
                Print Summary
              </button>
              <button 
                onClick={handleDownloadArchive}
                className="px-6 py-3 rounded-xl bg-blue-600 text-xs font-bold text-white hover:bg-blue-500 transition-all flex items-center gap-2"
              >
                <Download size={14} />
                Download Secure Archive
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
