import React, { useState } from 'react';
import {
  FileSpreadsheet,
  Rows3,
  Columns3,
  HardDrive,
  Copy,
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
  const totalCols = dataset.column_count;
  const duplicateRows = profile?.duplicate_rows;

  return (
    <div className="w-full rounded-xl border border-zinc-200 bg-white p-5 sm:p-6 shadow-xs">
      {/* Top row: Filename & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-4 border-b border-zinc-100">
        <div className="flex items-center space-x-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-zinc-100 text-zinc-700">
            <FileSpreadsheet className="h-5 w-5 text-indigo-600" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-base font-semibold text-zinc-950 truncate max-w-xs sm:max-w-md">
                {dataset.filename}
              </h2>
              <span className="inline-flex items-center rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-medium text-emerald-700 border border-emerald-200">
                <CheckCircle2 className="mr-1 h-3 w-3" /> Loaded
              </span>
            </div>
            <p className="text-xs text-zinc-500 font-mono mt-0.5">
              ID: {dataset.dataset_id.slice(0, 8)}...
            </p>
          </div>
        </div>

        <button
          onClick={onRemoveDataset}
          className="self-start sm:self-auto inline-flex items-center space-x-1.5 rounded-md border border-zinc-200 px-2.5 py-1.5 text-xs font-medium text-zinc-600 hover:bg-zinc-50 hover:text-red-600 hover:border-red-200 transition-colors cursor-pointer"
          title="Remove dataset and upload another"
        >
          <Trash2 className="h-3.5 w-3.5" />
          <span>Change dataset</span>
        </button>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 py-4 border-b border-zinc-100">
        {/* Rows */}
        <div className="flex items-center space-x-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-zinc-50 text-zinc-500">
            <Rows3 className="h-4 w-4" />
          </div>
          <div>
            <p className="text-xs text-zinc-500">Rows</p>
            <p className="text-base font-semibold text-zinc-900 tracking-tight font-mono">
              {Number(dataset.row_count).toLocaleString()}
            </p>
          </div>
        </div>

        {/* Columns */}
        <div className="flex items-center space-x-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-zinc-50 text-zinc-500">
            <Columns3 className="h-4 w-4" />
          </div>
          <div>
            <p className="text-xs text-zinc-500">Columns</p>
            <p className="text-base font-semibold text-zinc-900 tracking-tight font-mono">
              {totalCols}
            </p>
          </div>
        </div>

        {/* Memory */}
        <div className="flex items-center space-x-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-zinc-50 text-zinc-500">
            <HardDrive className="h-4 w-4" />
          </div>
          <div>
            <p className="text-xs text-zinc-500">Memory</p>
            <p className="text-base font-semibold text-zinc-900 tracking-tight font-mono">
              {dataset.memory_mb} MB
            </p>
          </div>
        </div>

        {/* Duplicate Rows / Column Breakdown */}
        <div className="flex items-center space-x-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-zinc-50 text-zinc-500">
            <Copy className="h-4 w-4" />
          </div>
          <div>
            <p className="text-xs text-zinc-500">Duplicates</p>
            <p className="text-base font-semibold text-zinc-900 tracking-tight font-mono">
              {duplicateRows !== undefined ? duplicateRows : '—'}
            </p>
          </div>
        </div>
      </div>

      {/* Feature Breakdown Pill Bar */}
      <div className="pt-4 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-zinc-500 font-medium">Features:</span>
          {numericCols.length > 0 && (
            <span className="inline-flex items-center rounded-md bg-indigo-50 px-2 py-1 text-xs font-medium text-indigo-700 border border-indigo-100">
              {numericCols.length} Numeric
            </span>
          )}
          {categoricalCols.length > 0 && (
            <span className="inline-flex items-center rounded-md bg-zinc-100 px-2 py-1 text-xs font-medium text-zinc-700 border border-zinc-200">
              {categoricalCols.length} Categorical
            </span>
          )}
          {isLoadingProfile && (
            <span className="text-zinc-400 italic">Profiling columns...</span>
          )}
        </div>

        {/* Expand buttons */}
        <div className="flex items-center space-x-2">
          {profile && profile.sample_rows && profile.sample_rows.length > 0 && (
            <button
              onClick={() => setShowSampleDrawer(!showSampleDrawer)}
              className="inline-flex items-center space-x-1 text-zinc-600 hover:text-zinc-900 font-medium transition-colors cursor-pointer"
            >
              <Table className="h-3.5 w-3.5" />
              <span>{showSampleDrawer ? 'Hide Sample' : 'Preview Sample'}</span>
            </button>
          )}

          <button
            onClick={() => setShowColumnsDrawer(!showColumnsDrawer)}
            className="inline-flex items-center space-x-1 text-indigo-600 hover:text-indigo-700 font-medium transition-colors cursor-pointer"
          >
            <span>{showColumnsDrawer ? 'Hide Schema' : 'View Columns'}</span>
            {showColumnsDrawer ? (
              <ChevronUp className="h-3.5 w-3.5" />
            ) : (
              <ChevronDown className="h-3.5 w-3.5" />
            )}
          </button>
        </div>
      </div>

      {/* Columns List Drawer */}
      {showColumnsDrawer && (
        <div className="mt-4 pt-4 border-t border-zinc-100">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 mb-2">
            Dataset Features ({dataset.columns.length})
          </h4>
          <div className="flex flex-wrap gap-1.5 max-h-48 overflow-y-auto p-1">
            {profile?.columns
              ? profile.columns.map((col) => (
                  <div
                    key={col.name}
                    className="inline-flex items-center space-x-1.5 rounded-md border border-zinc-200 bg-zinc-50 px-2 py-1 text-xs text-zinc-800"
                    title={`Type: ${col.dtype} | Nulls: ${col.null_count} (${col.null_percentage}%) | Unique: ${col.unique_count}`}
                  >
                    <span className="font-mono text-zinc-900">{col.name}</span>
                    <span
                      className={`text-[10px] px-1 rounded uppercase font-semibold ${
                        col.category === 'numeric'
                          ? 'bg-indigo-100 text-indigo-700'
                          : col.category === 'categorical'
                          ? 'bg-amber-100 text-amber-700'
                          : col.category === 'datetime'
                          ? 'bg-emerald-100 text-emerald-700'
                          : 'bg-zinc-200 text-zinc-600'
                      }`}
                    >
                      {col.category}
                    </span>
                    {col.null_percentage > 0 && (
                      <span className="text-[10px] text-red-600 font-mono">
                        {col.null_percentage}% null
                      </span>
                    )}
                  </div>
                ))
              : dataset.columns.map((colName) => (
                  <span
                    key={colName}
                    className="inline-block rounded-md border border-zinc-200 bg-zinc-50 px-2 py-1 font-mono text-xs text-zinc-700"
                  >
                    {colName}
                  </span>
                ))}
          </div>
        </div>
      )}

      {/* Data Sample Preview Drawer */}
      {showSampleDrawer && profile?.sample_rows && (
        <div className="mt-4 pt-4 border-t border-zinc-100">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 mb-2">
            First 5 Rows Preview
          </h4>
          <div className="overflow-x-auto rounded-lg border border-zinc-200">
            <table className="min-w-full divide-y divide-zinc-200 text-xs">
              <thead className="bg-zinc-50">
                <tr>
                  {dataset.columns.map((c) => (
                    <th
                      key={c}
                      className="px-3 py-2 text-left font-mono font-medium text-zinc-700 whitespace-nowrap"
                    >
                      {c}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100 bg-white">
                {profile.sample_rows.slice(0, 5).map((row, idx) => (
                  <tr key={idx} className="hover:bg-zinc-50/70 font-mono">
                    {dataset.columns.map((c) => (
                      <td
                        key={c}
                        className="px-3 py-1.5 text-zinc-600 whitespace-nowrap"
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
