import React from 'react';
import { SearchX, RefreshCw } from 'lucide-react';

interface EmptyStateProps {
  onReset: () => void;
  onRetry?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ onReset, onRetry }) => {
  return (
    <div className="w-full max-w-lg mx-auto rounded-xl border border-zinc-200 bg-white p-8 text-center shadow-xs">
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-zinc-100 text-zinc-500 mb-4">
        <SearchX className="h-6 w-6" />
      </div>

      <h3 className="text-lg font-semibold text-zinc-950">
        No strong discoveries found
      </h3>

      <p className="mt-2 text-sm text-zinc-600 leading-relaxed">
        DataPilot evaluated the candidate relationships and patterns in this
        dataset, but none passed its current statistical significance and variance
        thresholds.
      </p>

      <div className="mt-6 flex flex-col sm:flex-row items-center justify-center gap-3">
        {onRetry && (
          <button
            onClick={onRetry}
            className="w-full sm:w-auto inline-flex items-center justify-center space-x-1.5 rounded-lg border border-zinc-200 bg-white px-4 py-2 text-xs font-semibold text-zinc-700 shadow-2xs hover:bg-zinc-50 transition-colors cursor-pointer"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span>Retry Analysis</span>
          </button>
        )}

        <button
          onClick={onReset}
          className="w-full sm:w-auto inline-flex items-center justify-center space-x-1.5 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-2xs hover:bg-indigo-700 transition-colors cursor-pointer"
        >
          <span>Upload Another Dataset</span>
        </button>
      </div>
    </div>
  );
};
