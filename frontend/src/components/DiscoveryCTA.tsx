import React from 'react';
import { Compass, SlidersHorizontal } from 'lucide-react';

interface DiscoveryCTAProps {
  onDiscover: (maxFindings: number) => void;
  isDiscovering: boolean;
  maxFindings: number;
  onMaxFindingsChange: (val: number) => void;
}

export const DiscoveryCTA: React.FC<DiscoveryCTAProps> = ({
  onDiscover,
  isDiscovering,
  maxFindings,
  onMaxFindingsChange,
}) => {
  return (
    <div className="w-full rounded-xl border border-zinc-200 bg-white p-6 sm:p-8 text-center shadow-2xs">
      <div className="max-w-xl mx-auto space-y-3.5">
        <div className="inline-block text-[11px] font-mono uppercase tracking-widest text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded font-medium">
          Investigate This Dataset
        </div>

        <h3 className="text-xl sm:text-2xl font-semibold text-zinc-950 tracking-tight">
          Discover Hidden Patterns
        </h3>

        <p className="text-xs sm:text-sm text-zinc-600 leading-relaxed max-w-lg mx-auto">
          DataPilot will automatically investigate relationships, differences,
          patterns, and anomalies in this dataset.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-3">
          {/* Main Discover Button */}
          <button
            onClick={() => onDiscover(maxFindings)}
            disabled={isDiscovering}
            className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 rounded-lg bg-zinc-950 px-6 py-2.5 text-sm font-semibold text-white shadow-xs hover:bg-zinc-800 active:bg-zinc-900 disabled:opacity-50 disabled:cursor-not-allowed transition-all cursor-pointer group"
          >
            <Compass className="h-4 w-4 text-zinc-400 group-hover:text-white transition-colors" />
            <span>Discover Hidden Patterns</span>
          </button>

          {/* Top findings selector */}
          <div className="flex items-center space-x-1.5 text-xs text-zinc-500 bg-zinc-50 border border-zinc-200 rounded-lg px-3 py-2 shadow-2xs">
            <SlidersHorizontal className="h-3 w-3 text-zinc-400" />
            <span>Return</span>
            <select
              value={maxFindings}
              onChange={(e) => onMaxFindingsChange(Number(e.target.value))}
              disabled={isDiscovering}
              className="bg-transparent font-medium text-zinc-900 focus:outline-none cursor-pointer pr-1"
            >
              <option value={3}>3</option>
              <option value={5}>5</option>
              <option value={8}>8</option>
              <option value={10}>10</option>
            </select>
            <span>findings</span>
          </div>
        </div>

        <p className="text-[11px] text-zinc-400 pt-1 font-mono">
          Statistical evidence calculated by DataPilot • Interpretation by AI
        </p>
      </div>
    </div>
  );
};
