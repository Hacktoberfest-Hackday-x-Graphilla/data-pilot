import { useState } from 'react';
import {
  Filter,
  Sparkles,
} from 'lucide-react';
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

  const { summary, findings, filename } = report;

  const categories = [
    { id: 'all', label: 'All Findings', count: findings.length },
    {
      id: 'correlation',
      label: 'Relationships',
      count: findings.filter((f) => f.type === 'correlation').length,
    },
    {
      id: 'group_difference',
      label: 'Group Differences',
      count: findings.filter((f) => f.type === 'group_difference' || f.type === 'category_numeric').length,
    },
    {
      id: 'time_pattern',
      label: 'Time Patterns',
      count: findings.filter((f) => f.type === 'time_pattern').length,
    },
    {
      id: 'interaction',
      label: 'Interactions',
      count: findings.filter((f) => f.type === 'interaction').length,
    },
    {
      id: 'data_quality',
      label: 'Data Quality',
      count: findings.filter((f) => f.type === 'data_quality' || f.type === 'anomaly').length,
    },
  ].filter((c) => c.id === 'all' || c.count > 0);

  const filteredFindings =
    selectedFilter === 'all'
      ? findings
      : findings.filter((f) => {
          if (selectedFilter === 'group_difference') {
            return f.type === 'group_difference' || f.type === 'category_numeric';
          }
          if (selectedFilter === 'data_quality') {
            return f.type === 'data_quality' || f.type === 'anomaly';
          }
          return f.type === selectedFilter;
        });

  if (!findings || findings.length === 0) {
    return <EmptyState onReset={onReset} onRetry={onRunAgain} />;
  }

  return (
    <div className="w-full space-y-6">
      {/* Report Header */}
      <div className="rounded-xl border border-zinc-200 bg-white p-5 sm:p-6 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-5 border-b border-zinc-100">
          <div>
            <div className="flex items-center space-x-2">
              <span className="flex h-6 w-6 items-center justify-center rounded-md bg-indigo-600 text-white">
                <Sparkles className="h-3.5 w-3.5" />
              </span>
              <h2 className="text-xl font-semibold text-zinc-950 tracking-tight">
                Discovery Report
              </h2>
            </div>
            <p className="mt-1 text-xs sm:text-sm text-zinc-600">
              DataPilot investigated{' '}
              <span className="font-medium text-zinc-900">{filename}</span> and
              surfaced{' '}
              <span className="font-semibold text-indigo-700">
                {findings.length} findings
              </span>{' '}
              worth reviewing.
            </p>
          </div>

          <button
            onClick={onRunAgain}
            className="self-start sm:self-auto inline-flex items-center space-x-1.5 rounded-lg border border-zinc-200 bg-white px-3 py-1.5 text-xs font-semibold text-zinc-700 shadow-2xs hover:bg-zinc-50 transition-colors cursor-pointer"
          >
            <span>Re-analyze</span>
          </button>
        </div>

        {/* Real Summary Metrics Bar from Backend */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-4">
          <div className="bg-zinc-50 rounded-lg p-2.5 border border-zinc-100">
            <p className="text-[11px] text-zinc-500">Dataset Rows</p>
            <p className="text-sm font-semibold font-mono text-zinc-900 mt-0.5">
              {Number(summary.rows).toLocaleString()}
            </p>
          </div>

          <div className="bg-zinc-50 rounded-lg p-2.5 border border-zinc-100">
            <p className="text-[11px] text-zinc-500">Columns</p>
            <p className="text-sm font-semibold font-mono text-zinc-900 mt-0.5">
              {summary.columns}
            </p>
          </div>

          <div className="bg-zinc-50 rounded-lg p-2.5 border border-zinc-100">
            <p className="text-[11px] text-zinc-500">Patterns Examined</p>
            <p className="text-sm font-semibold font-mono text-indigo-700 mt-0.5">
              {summary.candidates_examined}
            </p>
          </div>

          <div className="bg-zinc-50 rounded-lg p-2.5 border border-zinc-100">
            <p className="text-[11px] text-zinc-500">Discoveries Returned</p>
            <p className="text-sm font-semibold font-mono text-emerald-700 mt-0.5">
              {summary.findings_returned}
            </p>
          </div>

          <div className="bg-zinc-50 rounded-lg p-2.5 border border-zinc-100 col-span-2 sm:col-span-1">
            <p className="text-[11px] text-zinc-500">Execution Time</p>
            <p className="text-sm font-semibold font-mono text-zinc-700 mt-0.5">
              {summary.execution_time_ms} ms
            </p>
          </div>
        </div>
      </div>

      {/* Filter Tabs if multiple categories exist */}
      {categories.length > 2 && (
        <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 text-xs">
          <span className="text-zinc-400 pl-1 pr-1 flex items-center">
            <Filter className="h-3 w-3 mr-1" />
            Filter:
          </span>
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedFilter(cat.id)}
              className={`inline-flex items-center space-x-1.5 rounded-full px-3 py-1 font-medium transition-colors cursor-pointer whitespace-nowrap ${
                selectedFilter === cat.id
                  ? 'bg-zinc-900 text-white shadow-2xs'
                  : 'bg-white text-zinc-600 border border-zinc-200 hover:bg-zinc-50 hover:text-zinc-900'
              }`}
            >
              <span>{cat.label}</span>
              <span
                className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                  selectedFilter === cat.id
                    ? 'bg-zinc-700 text-zinc-200'
                    : 'bg-zinc-100 text-zinc-600'
                }`}
              >
                {cat.count}
              </span>
            </button>
          ))}
        </div>
      )}

      {/* Discovery Cards Stack */}
      <div className="space-y-4">
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
