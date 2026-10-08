import React from 'react';
import { Sparkles, SlidersHorizontal } from 'lucide-react';

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
    <div className="w-full rounded-xl border border-indigo-100 bg-gradient-to-b from-indigo-50/50 to-white p-6 sm:p-8 text-center shadow-xs">
      <div className="max-w-xl mx-auto space-y-4">
        <div>
          <h3 className="text-xl font-semibold text-zinc-950 tracking-tight">
            Ready to uncover non-obvious patterns?
          </h3>
          <p className="mt-1.5 text-sm text-zinc-600 leading-relaxed">
            Let DataPilot investigate statistical relationships, subgroup differences,
            temporal cycles, and potential anomalies across this dataset.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
          {/* Main Discover Button */}
          <button
            onClick={() => onDiscover(maxFindings)}
            disabled={isDiscovering}
            className="w-full sm:w-auto inline-flex items-center justify-center space-x-2.5 rounded-lg bg-indigo-600 px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 active:bg-indigo-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all cursor-pointer group"
          >
            <Sparkles className="h-4 w-4 text-indigo-200 group-hover:scale-110 transition-transform" />
            <span>Discover Hidden Patterns</span>
          </button>

          {/* Finding Count Selector */}
          <div className="flex items-center space-x-1.5 text-xs text-zinc-500 bg-white border border-zinc-200 rounded-lg px-3 py-2.5 shadow-2xs">
            <SlidersHorizontal className="h-3.5 w-3.5 text-zinc-400" />
            <span>Top</span>
            <select
              value={maxFindings}
              onChange={(e) => onMaxFindingsChange(Number(e.target.value))}
              disabled={isDiscovering}
              className="bg-transparent font-medium text-zinc-800 focus:outline-none cursor-pointer pr-1"
            >
              <option value={3}>3</option>
              <option value={5}>5</option>
              <option value={8}>8</option>
              <option value={10}>10</option>
            </select>
            <span>findings</span>
          </div>
        </div>

        <p className="text-xs text-zinc-400 pt-1">
          Evidence is strictly computed via Python/Pandas • Explanations synthesized by AI
        </p>
      </div>
    </div>
  );
};
