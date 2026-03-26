import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, Mail, Lock, User as UserIcon, ArrowRight, CheckCircle2, ShieldAlert } from 'lucide-react';

export default function Login() {
  const { login, register, loading } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<'PATIENT' | 'DOCTOR' | 'ADMIN'>('PATIENT');
  const [isRegister, setIsRegister] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (isRegister) {
        await register(email, password, role);
      } else {
        await login(email, password);
      }
    } catch (err: any) {
      setError(err?.message || 'Authentication failed. Please check your credentials.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return (
    <div className="min-h-screen bg-[#020617] flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="w-12 h-12 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin"></div>
        <p className="text-slate-400 font-medium animate-pulse">Initializing Secure Session...</p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#020617] text-slate-100 flex flex-col md:flex-row relative overflow-hidden">
      {/* Background Blobs */}
      <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-blue-600/10 rounded-full blur-[120px] pointer-events-none"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-indigo-600/10 rounded-full blur-[120px] pointer-events-none"></div>

      {/* Left Side: Branding & Info (Hidden on mobile) */}
      <div className="hidden md:flex md:w-1/2 flex-col justify-center p-12 lg:p-24 z-10">
        <div className="flex items-center gap-3 mb-12">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white shadow-2xl shadow-blue-500/20">
            <ShieldCheck size={28} />
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-white">SecureMed</h2>
        </div>

        <h1 className="text-5xl lg:text-6xl font-extrabold tracking-tight text-white mb-8 leading-[1.1]">
          The Standard in <br />
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-500">
            Medical Privacy.
          </span>
        </h1>

        <div className="space-y-6 max-w-md">
          <div className="flex gap-4">
            <div className="mt-1 shrink-0 w-6 h-6 rounded-full bg-blue-500/10 flex items-center justify-center text-blue-400">
              <CheckCircle2 size={16} />
            </div>
            <div>
              <h3 className="font-bold text-slate-200">AES-256 Hybrid Encryption</h3>
              <p className="text-slate-400 text-sm mt-1">Military-grade protection for every DICOM record transmitted through our neural bridge.</p>
            </div>
          </div>
          <div className="flex gap-4">
            <div className="mt-1 shrink-0 w-6 h-6 rounded-full bg-blue-500/10 flex items-center justify-center text-blue-400">
              <CheckCircle2 size={16} />
            </div>
            <div>
              <h3 className="font-bold text-slate-200">Zero-Knowledge Architecture</h3>
              <p className="text-slate-400 text-sm mt-1">We never see your data. Only the intended recipient can decrypt and view sensitive imaging.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Right Side: Auth Form */}
      <div className="flex-1 flex items-center justify-center p-6 z-10">
        <div className="w-full max-w-md">
          <div className="bg-[#0f172a]/60 backdrop-blur-2xl p-8 md:p-10 rounded-[2rem] border border-slate-800/60 shadow-2xl relative">
            <div className="mb-8">
              <h2 className="text-3xl font-bold text-white mb-2">
                {isRegister ? 'Create Account' : 'Welcome Back'}
              </h2>
              <p className="text-slate-400">
                {isRegister ? 'Join our secure health network' : 'Enter your details to sign in'}
              </p>
            </div>

            {error && (
              <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-medium flex gap-3 items-center">
                <span className="text-lg">⚠️</span>
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-500 uppercase tracking-widest ml-1">Email Address</label>
                <div className="relative group">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-blue-500 transition-colors" size={18} />
                  <input
                    type="email"
                    placeholder="dr.smith@securemed.com"
                    className="w-full pl-12 pr-4 py-4 rounded-2xl bg-slate-900/50 border border-slate-800 focus:border-blue-500/50 focus:ring-4 focus:ring-blue-500/10 transition-all outline-none text-slate-200 placeholder:text-slate-600"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-500 uppercase tracking-widest ml-1">Password</label>
                <div className="relative group">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-blue-500 transition-colors" size={18} />
                  <input
                    type="password"
                    placeholder="••••••••••••"
                    className="w-full pl-12 pr-4 py-4 rounded-2xl bg-slate-900/50 border border-slate-800 focus:border-blue-500/50 focus:ring-4 focus:ring-blue-500/10 transition-all outline-none text-slate-200 placeholder:text-slate-600"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                </div>
              </div>

              {isRegister && (
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-widest ml-1">Professional Identity</label>
                  <div className="grid grid-cols-3 gap-2 p-1 bg-slate-900/80 rounded-2xl border border-slate-800">
                    <button
                      type="button"
                      onClick={() => setRole('PATIENT')}
                      className={`py-3 rounded-xl text-[10px] font-bold transition-all flex flex-col items-center justify-center gap-1 ${role === 'PATIENT' ? 'bg-slate-800 text-blue-400 shadow-lg border border-slate-700' : 'text-slate-500 hover:text-slate-300'}`}
                    >
                      <UserIcon size={14} />
                      Patient
                    </button>
                    <button
                      type="button"
                      onClick={() => setRole('DOCTOR')}
                      className={`py-3 rounded-xl text-[10px] font-bold transition-all flex flex-col items-center justify-center gap-1 ${role === 'DOCTOR' ? 'bg-slate-800 text-blue-400 shadow-lg border border-slate-700' : 'text-slate-500 hover:text-slate-300'}`}
                    >
                      <ShieldCheck size={14} />
                      Doctor
                    </button>
                    <button
                      type="button"
                      onClick={() => setRole('ADMIN')}
                      className={`py-3 rounded-xl text-[10px] font-bold transition-all flex flex-col items-center justify-center gap-1 ${role === 'ADMIN' ? 'bg-slate-800 text-blue-400 shadow-lg border border-slate-700' : 'text-slate-500 hover:text-slate-300'}`}
                    >
                      <ShieldAlert size={14} />
                      Admin
                    </button>
                  </div>
                </div>
              )}

              <button
                type="submit"
                disabled={submitting || loading}
                className="w-full mt-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold py-4 rounded-2xl shadow-xl shadow-blue-500/20 transition-all transform active:scale-[0.98] disabled:opacity-50 flex items-center justify-center gap-3 group"
              >
                {submitting ? (
                  <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                ) : (
                  <>
                    <span>{isRegister ? 'Establish Account' : 'Secure Authorization'}</span>
                    <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
                  </>
                )}
              </button>
            </form>

            <div className="mt-10 text-center">
              <p className="text-slate-500 text-sm font-medium">
                {isRegister ? 'Already a member?' : 'New to SecureMed?'}
                <button
                  type="button"
                  onClick={() => setIsRegister(!isRegister)}
                  className="ml-2 text-blue-400 hover:text-blue-300 font-bold transition-colors underline underline-offset-4"
                >
                  {isRegister ? 'Sign In' : 'Create Account'}
                </button>
              </p>
            </div>
          </div>

          <p className="mt-8 text-center text-[10px] text-slate-600 uppercase tracking-widest font-bold">
            Protected by Advanced Cryptography & HIPAA Compliant
          </p>
        </div>
      </div>
    </div>
  );
}


