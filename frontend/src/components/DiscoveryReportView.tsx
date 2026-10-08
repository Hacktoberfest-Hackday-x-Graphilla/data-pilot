import { useState } from 'react';
import type { DiscoveryResponse } from '../api/types';
import { DiscoveryCard } from './DiscoveryCard';
import { EmptyState } from './EmptyState';

interface DiscoveryReportViewProps {
  report: DiscoveryResponse;
  onRunAgain: () => void;
  onReset: () => void;
}

export const DiscoveryReportView: React.FC<DiscoveryReportViewProps> = ({
  report,
  onRunAgain,
  onReset,
}) => {
  const [selectedFilter, setSelectedFilter] = useState<string>('all');

  const { summary, findings } = report;

  const categories = [
    { id: 'all', label: 'All Findings', count: findings.length },
    {
      id: 'correlation',
      label: 'Relationships',
      count: findings.filter((f) => f.type === 'correlation').length,
    },
    {
      id: 'difference',
      label: 'Differences',
      count: findings.filter((f) => f.type === 'group_difference' || f.type === 'category_numeric').length,
    },
    {
      id: 'pattern',
      label: 'Patterns',
      count: findings.filter((f) => f.type === 'time_pattern' || f.type === 'interaction').length,
    },
    {
      id: 'quality',
      label: 'Quality & Anomalies',
      count: findings.filter((f) => f.type === 'data_quality' || f.type === 'anomaly').length,
    },
  ].filter((c) => c.id === 'all' || c.count > 0);

  const filteredFindings =
    selectedFilter === 'all'
      ? findings
      : findings.filter((f) => {
          if (selectedFilter === 'difference') {
            return f.type === 'group_difference' || f.type === 'category_numeric';
          }
          if (selectedFilter === 'pattern') {
            return f.type === 'time_pattern' || f.type === 'interaction';
          }
          if (selectedFilter === 'quality') {
            return f.type === 'data_quality' || f.type === 'anomaly';
          }
          return f.type === selectedFilter;
        });

  if (!findings || findings.length === 0) {
    return <EmptyState onReset={onReset} onRetry={onRunAgain} />;
  }

  return (
    <div className="w-full space-y-4">
      {/* Report Header & Compact Metrics Strip */}
      <div className="rounded-xl border border-zinc-200 bg-white p-4 sm:p-5 shadow-2xs">
        <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-2 pb-3 border-b border-zinc-100">
          <div>
            <div className="inline-block text-[10px] font-mono uppercase tracking-widest text-indigo-700 bg-indigo-50 px-2 py-0.2 rounded font-medium mb-1">
              Discovery Report
            </div>
            <h2 className="text-base sm:text-lg font-semibold text-zinc-950 tracking-tight">
              DataPilot investigated your dataset
            </h2>
            <p className="text-xs text-zinc-600 mt-0.5">
              Surfaced the findings most worth your attention based on statistical evidence.
            </p>
          </div>

          <button
            onClick={onRunAgain}
            className="self-start sm:self-auto inline-flex items-center space-x-1 rounded border border-zinc-200 bg-white px-2.5 py-1 text-xs font-medium text-zinc-700 hover:bg-zinc-50 transition-colors cursor-pointer"
          >
            <span>Re-run discovery</span>
          </button>
        </div>

        {/* Clean Single Metrics Strip (Not huge dashboard boxes) */}
        <div className="flex flex-wrap items-center divide-x divide-zinc-200 pt-3 text-xs">
          <div className="pr-4 py-1">
            <span className="text-zinc-500 text-[11px]">Rows:</span>{' '}
            <strong className="font-mono text-zinc-900 ml-1">
              {Number(summary.rows).toLocaleString()}
            </strong>
          </div>

          <div className="px-4 py-1">
            <span className="text-zinc-500 text-[11px]">Columns:</span>{' '}
            <strong className="font-mono text-zinc-900 ml-1">
              {summary.columns}
            </strong>
          </div>

          <div className="px-4 py-1">
            <span className="text-zinc-500 text-[11px]">Relationships Tested:</span>{' '}
            <strong className="font-mono text-zinc-900 ml-1">
              {summary.candidates_examined}
            </strong>
          </div>

          <div className="px-4 py-1">
            <span className="text-zinc-500 text-[11px]">Findings:</span>{' '}
            <strong className="font-mono text-indigo-700 ml-1">
              {summary.findings_returned}
            </strong>
          </div>

          <div className="pl-4 py-1 hidden sm:block">
            <span className="text-zinc-400 text-[11px]">Runtime:</span>{' '}
            <span className="font-mono text-zinc-500 text-[11px] ml-1">
              {summary.execution_time_ms} ms
            </span>
          </div>
        </div>
      </div>

      {/* Simplified Filter Bar */}
      {categories.length > 2 && (
        <div className="flex items-center space-x-1 overflow-x-auto pb-0.5 text-xs">
          <span className="text-zinc-400 text-[11px] pr-1.5 font-medium">Filter:</span>
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedFilter(cat.id)}
              className={`inline-flex items-center space-x-1.5 rounded-md px-2.5 py-1 text-xs font-medium transition-colors cursor-pointer whitespace-nowrap ${
                selectedFilter === cat.id
                  ? 'bg-zinc-900 text-white'
                  : 'bg-white text-zinc-600 border border-zinc-200 hover:bg-zinc-50'
              }`}
            >
              <span>{cat.label}</span>
              <span
                className={`text-[10px] px-1 py-0.1 rounded font-mono ${
                  selectedFilter === cat.id
                    ? 'bg-zinc-800 text-zinc-200'
                    : 'bg-zinc-100 text-zinc-600'
                }`}
              >
                {cat.count}
              </span>
            </button>
          ))}
        </div>
      )}

      {/* Discovery Cards: THE HERO OF THE PRODUCT */}
      <div className="space-y-3.5">
        {filteredFindings.map((finding, index) => (
          <DiscoveryCard
            key={finding.id || index}
            finding={finding}
            orderNumber={index + 1}
          />
        ))}
      </div>
    </div>
  );
};
