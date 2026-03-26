import axios from "axios";

export const RAW_API = (import.meta.env.VITE_API_BASE || import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000').trim().replace(/\/\/$/, '');
export const API_BASE = RAW_API.replace(/([^:])\/\//g, '$1/');

export const API = axios.create({
  baseURL: API_BASE,
  withCredentials: false,
});

API.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token && config.headers) {
    (config.headers as any).Authorization = `Bearer ${token}`;
  }
  return config;
});

API.interceptors.response.use(
  (res) => res,
  (err) => {
    // Log helpful information without throwing undefined access errors
    try {
      console.error("API Error:", err.response?.data || err.message);
    } catch (e) {
      console.error("API Error (unknown):", err);
    }
    return Promise.reject(err);
  }
);


export type FileItem = {
  id: number;
  sender: string;
  filename: string;
  status: string;
  created_at?: string;
};

export const getInbox = () => API.get<FileItem[]>("/patient/inbox");

export const getDoctorInbox = () => API.get<FileItem[]>("/doctor/inbox");

export const decryptFile = (recordId: number) => API.post(`/patient/decrypt/${recordId}`);

export const decryptDoctorFile = (recordId: number) => API.post(`/doctor/decrypt/${recordId}`);

export const sendDoctorFile = (formData: FormData) => API.post("/doctor/send", formData);

export const sendPatientFile = (formData: FormData) => API.post("/patient/send", formData);

export const getDoctorRecords = () => API.get("/doctor/records");

export const getDoctorPatients = () => API.get("/doctor/patients");

export const getProviders = () => API.get("/patient/providers");

export const getRecordDetails = (recordId: number) => API.get(`/patient/record/${recordId}`);

export const deletePatientRecord = (recordId: number) => API.delete(`/patient/record/${recordId}`);

export const revokeDoctorRecord = (recordId: number) => API.delete(`/doctor/record/${recordId}`);


