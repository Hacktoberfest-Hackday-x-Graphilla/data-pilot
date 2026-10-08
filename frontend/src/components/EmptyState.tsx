import React from 'react';
import { SearchX, RefreshCw } from 'lucide-react';

interface EmptyStateProps {
  onReset: () => void;
  onRetry?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ onReset, onRetry }) => {
  return (
    <div className="w-full max-w-md mx-auto rounded-xl border border-zinc-200 bg-white p-7 text-center shadow-2xs">
      <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-md bg-zinc-100 text-zinc-600 mb-3.5">
        <SearchX className="h-5 w-5" />
      </div>

      <div className="text-[10px] font-mono uppercase tracking-widest text-zinc-500 mb-1">
        Evaluation Complete
      </div>
      <h3 className="text-base font-semibold text-zinc-950">
        No strong discoveries found
      </h3>

      <p className="mt-2 text-xs text-zinc-600 leading-relaxed">
        DataPilot investigated this dataset, but did not find relationships
        that passed its current significance and variance thresholds.
      </p>

      <div className="mt-5 flex flex-col sm:flex-row items-center justify-center gap-2.5">
        {onRetry && (
          <button
            onClick={onRetry}
            className="w-full sm:w-auto inline-flex items-center justify-center space-x-1.5 rounded-md border border-zinc-200 bg-white px-3 py-1.5 text-xs font-medium text-zinc-700 hover:bg-zinc-50 transition-colors cursor-pointer"
          >
            <RefreshCw className="h-3 w-3" />
            <span>Retry analysis</span>
          </button>
        )}

        <button
          onClick={onReset}
          className="w-full sm:w-auto inline-flex items-center justify-center space-x-1.5 rounded-md bg-zinc-950 px-3 py-1.5 text-xs font-medium text-white hover:bg-zinc-800 transition-colors cursor-pointer"
        >
          <span>Try another dataset</span>
        </button>
      </div>
    </div>
  );
};
