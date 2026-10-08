import React, { useState } from 'react';
import {
  FileSpreadsheet,
  ChevronDown,
  ChevronUp,
  Table,
  CheckCircle2,
  Trash2,
} from 'lucide-react';
import type { DatasetSummary, ProfileReport } from '../api/types';

interface DatasetOverviewProps {
  dataset: DatasetSummary;
  profile: ProfileReport | null;
  isLoadingProfile: boolean;
  onRemoveDataset: () => void;
}

export const DatasetOverview: React.FC<DatasetOverviewProps> = ({
  dataset,
  profile,
  isLoadingProfile,
  onRemoveDataset,
}) => {
  const [showColumnsDrawer, setShowColumnsDrawer] = useState(false);
  const [showSampleDrawer, setShowSampleDrawer] = useState(false);

  const numericCols = profile?.numeric_columns || [];
  const categoricalCols = profile?.categorical_columns || [];
  const datetimeCols = profile?.columns.filter((c) => c.category === 'datetime') || [];
  const duplicateRows = profile?.duplicate_rows;

  return (
    <div className="w-full rounded-xl border border-zinc-200 bg-white p-4 sm:p-5 shadow-2xs">
      {/* Top Header: Filename & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2.5 pb-3.5 border-b border-zinc-100">
        <div className="flex items-center space-x-2.5 min-w-0">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-zinc-100 text-zinc-700">
            <FileSpreadsheet className="h-4 w-4 text-indigo-600" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center space-x-2">
              <h2 className="text-sm font-semibold text-zinc-950 truncate max-w-xs sm:max-w-md">
                {dataset.filename}
              </h2>
              <span className="inline-flex items-center rounded-full bg-emerald-50 px-2 py-0.2 text-[10px] font-medium text-emerald-700 border border-emerald-200 shrink-0">
                <CheckCircle2 className="mr-1 h-2.5 w-2.5" /> Ready
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {profile && profile.sample_rows && profile.sample_rows.length > 0 && (
            <button
              onClick={() => setShowSampleDrawer(!showSampleDrawer)}
              className="inline-flex items-center space-x-1 text-xs text-zinc-600 hover:text-zinc-900 px-2 py-1 rounded hover:bg-zinc-50 transition-colors cursor-pointer"
            >
              <Table className="h-3 w-3" />
              <span>{showSampleDrawer ? 'Hide Preview' : 'Preview Data'}</span>
            </button>
          )}

          <button
            onClick={() => setShowColumnsDrawer(!showColumnsDrawer)}
            className="inline-flex items-center space-x-1 text-xs text-zinc-600 hover:text-zinc-900 px-2 py-1 rounded hover:bg-zinc-50 transition-colors cursor-pointer"
          >
            <span>{showColumnsDrawer ? 'Hide Schema' : 'Inspect Columns'}</span>
            {showColumnsDrawer ? (
              <ChevronUp className="h-3 w-3" />
            ) : (
              <ChevronDown className="h-3 w-3" />
            )}
          </button>

          <button
            onClick={onRemoveDataset}
            className="inline-flex items-center space-x-1 rounded border border-zinc-200 px-2 py-1 text-xs text-zinc-500 hover:text-rose-600 hover:border-rose-200 transition-colors cursor-pointer"
            title="Change dataset"
          >
            <Trash2 className="h-3 w-3" />
            <span>Remove</span>
          </button>
        </div>
      </div>

      {/* Compact Metrics Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 pt-3 text-xs">
        <div className="bg-zinc-50/70 rounded-md p-2 border border-zinc-100">
          <p className="text-[10px] text-zinc-500 uppercase tracking-wider font-mono">Rows</p>
          <p className="text-sm font-semibold text-zinc-900 font-mono mt-0.5">
            {Number(dataset.row_count).toLocaleString()}
          </p>
        </div>

        <div className="bg-zinc-50/70 rounded-md p-2 border border-zinc-100">
          <p className="text-[10px] text-zinc-500 uppercase tracking-wider font-mono">Columns</p>
          <p className="text-sm font-semibold text-zinc-900 font-mono mt-0.5">
            {dataset.column_count}
          </p>
        </div>

        <div className="bg-zinc-50/70 rounded-md p-2 border border-zinc-100">
          <p className="text-[10px] text-zinc-500 uppercase tracking-wider font-mono">Features</p>
          <p className="text-xs font-medium text-zinc-700 mt-1">
            {isLoadingProfile ? (
              <span className="text-zinc-400 italic">Detecting...</span>
            ) : (
              <span>
                <strong className="text-zinc-900">{numericCols.length}</strong> num,{' '}
                <strong className="text-zinc-900">{categoricalCols.length}</strong> cat
                {datetimeCols.length > 0 && `, ${datetimeCols.length} time`}
              </span>
            )}
          </p>
        </div>

        <div className="bg-zinc-50/70 rounded-md p-2 border border-zinc-100">
          <p className="text-[10px] text-zinc-500 uppercase tracking-wider font-mono">Duplicates</p>
          <p className="text-sm font-semibold text-zinc-800 font-mono mt-0.5">
            {duplicateRows !== undefined ? duplicateRows : '0'}
          </p>
        </div>

        <div className="bg-zinc-50/70 rounded-md p-2 border border-zinc-100 col-span-2 sm:col-span-1">
          <p className="text-[10px] text-zinc-500 uppercase tracking-wider font-mono">Memory</p>
          <p className="text-sm font-semibold text-zinc-800 font-mono mt-0.5">
            {dataset.memory_mb} MB
          </p>
        </div>
      </div>

      {/* Columns List Drawer */}
      {showColumnsDrawer && (
        <div className="mt-3 pt-3 border-t border-zinc-100">
          <h4 className="text-[11px] font-semibold uppercase tracking-wider text-zinc-500 mb-2 font-mono">
            Columns ({dataset.columns.length})
          </h4>
          <div className="flex flex-wrap gap-1.5 max-h-40 overflow-y-auto p-0.5">
            {profile?.columns
              ? profile.columns.map((col) => (
                  <div
                    key={col.name}
                    className="inline-flex items-center space-x-1.5 rounded border border-zinc-200 bg-zinc-50 px-2 py-0.5 text-xs text-zinc-800"
                    title={`Type: ${col.dtype} | Nulls: ${col.null_count} (${col.null_percentage}%) | Unique: ${col.unique_count}`}
                  >
                    <span className="font-mono text-zinc-900">{col.name}</span>
                    <span
                      className={`text-[9px] px-1 rounded uppercase font-semibold ${
                        col.category === 'numeric'
                          ? 'bg-indigo-50 text-indigo-700 border border-indigo-100'
                          : col.category === 'categorical'
                          ? 'bg-zinc-200 text-zinc-700'
                          : col.category === 'datetime'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-100'
                          : 'bg-zinc-100 text-zinc-600'
                      }`}
                    >
                      {col.category}
                    </span>
                    {col.null_percentage > 0 && (
                      <span className="text-[9px] text-rose-600 font-mono">
                        {col.null_percentage}% null
                      </span>
                    )}
                  </div>
                ))
              : dataset.columns.map((colName) => (
                  <span
                    key={colName}
                    className="inline-block rounded border border-zinc-200 bg-zinc-50 px-2 py-0.5 font-mono text-xs text-zinc-700"
                  >
                    {colName}
                  </span>
                ))}
          </div>
        </div>
      )}

      {/* Data Sample Preview Drawer */}
      {showSampleDrawer && profile?.sample_rows && (
        <div className="mt-3 pt-3 border-t border-zinc-100">
          <h4 className="text-[11px] font-semibold uppercase tracking-wider text-zinc-500 mb-2 font-mono">
            Sample Preview (First 5 Rows)
          </h4>
          <div className="overflow-x-auto rounded border border-zinc-200">
            <table className="min-w-full divide-y divide-zinc-200 text-xs">
              <thead className="bg-zinc-50">
                <tr>
                  {dataset.columns.map((c) => (
                    <th
                      key={c}
                      className="px-2.5 py-1.5 text-left font-mono font-medium text-zinc-700 whitespace-nowrap text-[11px]"
                    >
                      {c}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100 bg-white">
                {profile.sample_rows.slice(0, 5).map((row, idx) => (
                  <tr key={idx} className="hover:bg-zinc-50/70 font-mono text-[11px]">
                    {dataset.columns.map((c) => (
                      <td
                        key={c}
                        className="px-2.5 py-1 text-zinc-600 whitespace-nowrap"
                      >
                        {row[c] !== null && row[c] !== undefined
                          ? String(row[c])
                          : 'null'}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
