import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingOverlayProps {
  message?: string;
  className?: string;
}

const LoadingOverlay: React.FC<LoadingOverlayProps> = ({ message = 'Loading...', className = '' }) => {
  return (
    <div className={`fixed inset-0 z-[100] flex items-center justify-center bg-[#020617]/80 backdrop-blur-sm ${className}`}>
      <div className="text-center">
        <div className="relative mb-6">
          <div className="w-16 h-16 rounded-full border-4 border-blue-500/20 animate-pulse mx-auto" />
          <div className="absolute inset-0 flex items-center justify-center text-blue-500 animate-spin">
            <Loader2 size={32} />
          </div>
        </div>
        <p className="text-lg font-medium text-white tracking-tight animate-pulse">
          {message}
        </p>
      </div>
    </div>
  );
};

export default LoadingOverlay;
