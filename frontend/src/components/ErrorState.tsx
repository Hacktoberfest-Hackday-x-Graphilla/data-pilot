import React from 'react';
import { AlertOctagon, RefreshCw, UploadCloud } from 'lucide-react';

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  onReset: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Analysis encountered an issue',
  message,
  onRetry,
  onReset,
}) => {
  return (
    <div className="w-full max-w-lg mx-auto rounded-xl border border-red-200 bg-red-50/40 p-6 sm:p-8 text-center shadow-xs">
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-red-100 text-red-600 mb-4">
        <AlertOctagon className="h-6 w-6" />
      </div>

      <h3 className="text-lg font-semibold text-zinc-950">{title}</h3>

      <p className="mt-2 text-sm text-zinc-600 leading-relaxed font-normal">
        {message}
      </p>

      <div className="mt-6 flex flex-col sm:flex-row items-center justify-center gap-3">
        {onRetry && (
          <button
            onClick={onRetry}
            className="w-full sm:w-auto inline-flex items-center justify-center space-x-1.5 rounded-lg bg-zinc-900 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-zinc-800 transition-colors cursor-pointer"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span>Try Again</span>
          </button>
        )}

        <button
          onClick={onReset}
          className="w-full sm:w-auto inline-flex items-center justify-center space-x-1.5 rounded-lg border border-zinc-200 bg-white px-4 py-2 text-xs font-semibold text-zinc-700 shadow-2xs hover:bg-zinc-50 transition-colors cursor-pointer"
        >
          <UploadCloud className="h-3.5 w-3.5" />
          <span>Upload Another Dataset</span>
        </button>
      </div>
    </div>
  );
};
