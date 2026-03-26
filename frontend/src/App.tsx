import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Link, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from './context/AuthContext';
import ErrorBoundary from './components/ErrorBoundary';
import Patient from "./pages/Patient";
import Doctor from "./pages/Doctor";
import Login from "./pages/Login";
import Admin from "./pages/Admin";
import { 
  LayoutDashboard, 
  FileUp, 
  ShieldCheck, 
  LogOut, 
  Menu, 
  User as UserIcon,
  Bell,
  Search,
  Activity
} from 'lucide-react';

// Protected Route Component
const ProtectedRoute = ({ children, allowedRole }: { children: React.ReactNode; allowedRole: 'PATIENT' | 'DOCTOR' | 'ADMIN' }) => {
  const { role, token } = useAuth();
  if (!token) return <Navigate to="/login" replace />;
  if (role !== allowedRole) return <Navigate to="/" replace />;
  return <>{children}</>;
};

// Sidebar Link Component
const SidebarLink = ({ to, icon: Icon, label, active, onClick }: { to: string; icon: any; label: string; active: boolean; onClick?: () => void }) => (
  <Link
    to={to}
    onClick={onClick}
    className={`nav-link ${active ? 'nav-link-active' : 'nav-link-inactive'}`}
  >
    <Icon size={20} className={active ? 'text-white' : 'text-slate-500 group-hover:text-blue-400 transition-colors'} />
    <span className="font-medium tracking-tight">{label}</span>
  </Link>
);

function Layout({ children }: { children: React.ReactNode }) {
  const { token, logout, role, email } = useAuth();
  const location = useLocation();
  const [isSidebarOpen, setSidebarOpen] = useState(false);

  if (!token) return <>{children}</>;

  const pageTitle = () => {
    switch (location.pathname) {
      case '/': return role === 'DOCTOR' ? 'Dashboard' : 'Medical Inbox';
      case '/doctor': return 'Upload Records';
      case '/admin': return 'System Overview';
      default: return 'SecureMed';
    }
  };

  return (
    <div className="flex min-h-screen bg-[#020617] font-sans selection:bg-blue-500/30 text-slate-100">
      {/* Sidebar Overlay */}
      {isSidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`fixed inset-y-0 left-0 z-50 w-72 bg-[#0f172a]/80 backdrop-blur-3xl border-r border-slate-800/40 transition-all duration-300 transform ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'} md:translate-x-0`}>
        <div className="flex flex-col h-full">
          {/* Logo Section */}
          <div className="p-8 border-b border-slate-800/40">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white shadow-xl shadow-blue-500/20">
                <ShieldCheck size={24} />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white tracking-tight">SecureMed</h1>
                <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest leading-none mt-1">Health Records</p>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-6 space-y-2 overflow-y-auto custom-scrollbar">
            <p className="text-[10px] font-bold text-slate-600 uppercase tracking-[0.2em] mb-4 px-2">Main Menu</p>
            
            {(role === 'PATIENT' || role === 'ADMIN') && (
              <SidebarLink 
                to="/" 
                icon={LayoutDashboard} 
                label="Inbox" 
                active={location.pathname === '/'}
                onClick={() => setSidebarOpen(false)}
              />
            )}
            {(role === 'DOCTOR' || role === 'ADMIN') && (
              <SidebarLink 
                to="/doctor" 
                icon={FileUp} 
                label="Transfer" 
                active={location.pathname === '/doctor'}
                onClick={() => setSidebarOpen(false)}
              />
            )}
            {role === 'ADMIN' && (
              <SidebarLink 
                to="/admin" 
                icon={Activity} 
                label="Security Hub" 
                active={location.pathname === '/admin'}
                onClick={() => setSidebarOpen(false)}
              />
            )}
          </nav>

          {/* User & Logout */}
          <div className="p-6 border-t border-slate-800/40 bg-slate-900/20">
            <div className="flex items-center gap-3 mb-6 p-2 rounded-xl bg-slate-800/30 border border-slate-700/30">
              <div className="w-10 h-10 rounded-lg bg-slate-700 flex items-center justify-center text-slate-300 shrink-0">
                <UserIcon size={20} />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-semibold text-slate-200 truncate">{email?.split('@')[0]}</p>
                <p className="text-[10px] text-blue-400 font-bold uppercase tracking-tighter">{role}</p>
              </div>
            </div>
            <button 
              onClick={logout}
              className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-slate-400 hover:text-red-400 hover:bg-red-500/5 transition-all duration-200 font-medium group"
            >
              <LogOut size={18} className="group-hover:translate-x-1 transition-transform" />
              <span>Sign Out</span>
            </button>
          </div>
        </div>
      </aside>

      {/* Content Area */}
      <div className="flex-1 md:ml-72 flex flex-col min-h-screen">
        {/* Topbar */}
        <header className="sticky top-0 z-30 h-20 bg-[#020617]/80 backdrop-blur-xl border-b border-slate-800/40 px-6 md:px-10 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button 
              onClick={() => setSidebarOpen(true)}
              className="md:hidden p-2 text-slate-400 hover:text-white transition-colors"
            >
              <Menu size={24} />
            </button>
            <h2 className="text-xl font-bold text-white tracking-tight">{pageTitle()}</h2>
          </div>

          <div className="flex items-center gap-3 md:gap-6">
            <div className="hidden lg:flex items-center gap-2 bg-slate-900/50 border border-slate-800/60 px-4 py-2 rounded-xl w-64 focus-within:border-blue-500/50 transition-all">
              <Search size={16} className="text-slate-500" />
              <input 
                type="text" 
                placeholder="Search records..." 
                className="bg-transparent border-none outline-none text-sm text-slate-300 placeholder:text-slate-600 w-full"
                onChange={(e) => {
                  // Global search placeholder
                  console.log("Global search:", e.target.value);
                }}
              />
            </div>
            <button 
              onClick={() => alert("No new security notifications.")}
              className="p-2.5 rounded-xl bg-slate-900/50 border border-slate-800/60 text-slate-400 hover:text-blue-400 hover:border-blue-500/30 transition-all relative"
            >
              <Bell size={20} />
              <span className="absolute top-2 right-2 w-2 h-2 bg-blue-500 rounded-full border-2 border-[#020617]"></span>
            </button>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-6 md:p-10">
          {children}
        </main>
      </div>
    </div>
  );
}

function AppContent() {
  const { token, role } = useAuth();

  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/login" element={!token ? <Login /> : <Navigate to="/" replace />} />
          <Route path="/" element={
            token ? (
              role === 'ADMIN' ? <Navigate to="/admin" replace /> :
              role === 'DOCTOR' ? <Navigate to="/doctor" replace /> : <Patient />
            ) : <Navigate to="/login" replace />
          } />
          <Route path="/doctor" element={
            <ProtectedRoute allowedRole="DOCTOR">
              <Doctor />
            </ProtectedRoute>
          } />
          <Route path="/admin" element={
            <ProtectedRoute allowedRole="ADMIN">
              <Admin />
            </ProtectedRoute>
          } />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;

