import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
interface LoginResponse {
  token: string;
  role: string;
  email?: string;
}

interface AuthContextType {
  token: string | null;
  role: string | null;
  email: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, role: 'PATIENT' | 'DOCTOR' | 'ADMIN') => Promise<void>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const RAW_API = (import.meta.env.VITE_API_BASE || import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000').trim().replace(/\/\/$/, '');
// normalize: remove any trailing slash and strip a trailing /api/v1 if present
const API_ROOT = RAW_API.replace(/\/api\/v1\/?$/i, '').replace(/\/+$/,'');
const AUTH_BASE = `${API_ROOT}/api/v1/auth`.replace(/([^:])\/\//g, '$1/');

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [token, setToken] = useState<string | null>(null);
  const [role, setRole] = useState<string | null>(null);
  const [email, setEmail] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    try {
      const savedToken = localStorage.getItem('token');
      const savedRole = localStorage.getItem('role');
      const savedEmail = localStorage.getItem('email');
      if (savedToken) setToken(savedToken);
      if (savedRole) setRole(savedRole);
      if (savedEmail) setEmail(savedEmail);
    } finally {
      setLoading(false);
    }
  }, []);

  const saveAuth = (data: LoginResponse, userEmail: string) => {
    if (!data || !data.token) return;
    localStorage.setItem('token', data.token);
    if (data.role) localStorage.setItem('role', data.role);
    localStorage.setItem('email', userEmail);
    setToken(data.token);
    if (data.role) setRole(data.role);
    setEmail(userEmail);
  };

  const login = async (email: string, password: string) => {
    const res = await fetch(`${AUTH_BASE}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error((data && (data.error || data.message)) || 'Login failed');
    saveAuth(data as LoginResponse, email);
  };

  const register = async (email: string, password: string, role: 'PATIENT' | 'DOCTOR' | 'ADMIN') => {
    const res = await fetch(`${AUTH_BASE}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, role }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error((data && (data.error || data.message)) || 'Registration failed');
    // auto-login after register
    await login(email, password);
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    localStorage.removeItem('email');
    setToken(null);
    setRole(null);
    setEmail(null);
  };

  return (
    <AuthContext.Provider value={{ token, role, email, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};

