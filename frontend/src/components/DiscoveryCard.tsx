import React, { useState } from 'react';
import {
  TrendingUp,
  GitCompare,
  Clock,
  Layers,
  AlertTriangle,
  FileSearch,
  Sparkles,
  Calculator,
  ShieldAlert,
  ChevronDown,
  ChevronUp,
  Code2,
  Copy,
  Check,
} from 'lucide-react';
import { DiscoveryFinding } from '../api/types';
import { VisualCallout } from './VisualCallout';

interface DiscoveryCardProps {
  finding: DiscoveryFinding;
  orderNumber: number;
}

export const DiscoveryCard: React.FC<DiscoveryCardProps> = ({
  finding,
  orderNumber,
}) => {
  const [isEvidenceExpanded, setIsEvidenceExpanded] = useState(false);
  const [showRawJson, setShowRawJson] = useState(false);
  const [hasCopied, setHasCopied] = useState(false);

  const {
    id,
    type,
    title,
    columns,
    metric,
    evidence,
    explanation,
    caution,
    importance,
    discovery_score,
  } = finding;

  // Category Badge Config
  const getTypeConfig = (category: string) => {
    switch (category) {
      case 'correlation':
        return {
          label: 'RELATIONSHIP',
          icon: TrendingUp,
          bg: 'bg-blue-50 text-blue-700 border-blue-200',
        };
      case 'group_difference':
        return {
          label: 'GROUP DIFFERENCE',
          icon: GitCompare,
          bg: 'bg-emerald-50 text-emerald-700 border-emerald-200',
        };
      case 'time_pattern':
        return {
          label: 'TIME PATTERN',
          icon: Clock,
          bg: 'bg-violet-50 text-violet-700 border-violet-200',
        };
      case 'interaction':
        return {
          label: 'INTERACTION',
          icon: Layers,
          bg: 'bg-indigo-50 text-indigo-700 border-indigo-200',
        };
      case 'data_quality':
      case 'anomaly':
        return {
          label: 'DATA QUALITY',
          icon: AlertTriangle,
          bg: 'bg-amber-50 text-amber-700 border-amber-200',
        };
      case 'category_numeric':
        return {
          label: 'SUBGROUP DIVERGENCE',
          icon: GitCompare,
          bg: 'bg-teal-50 text-teal-700 border-teal-200',
        };
      default:
        return {
          label: (category || 'PATTERN').toUpperCase().replace('_', ' '),
          icon: FileSearch,
          bg: 'bg-zinc-100 text-zinc-700 border-zinc-200',
        };
    }
  };

  const typeConfig = getTypeConfig(type);
  const TypeIcon = typeConfig.icon;

  // Python-computed evidence narrative
  const pythonEvidenceText =
    evidence?.description ||
    (type === 'correlation'
      ? `Pearson correlation computed across ${
          metric?.sample_size
            ? Number(metric.sample_size).toLocaleString()
            : 'all'
        } valid pairs (r = ${metric?.correlation}, p-value = ${
          metric?.p_value ?? '<0.001'
        }).`
      : type === 'group_difference'
      ? `Subgroup '${metric?.group}' (n = ${
          metric?.group_size
            ? Number(metric.group_size).toLocaleString()
            : 'N/A'
        }) displays mean ${metric?.group_mean} versus population mean ${
          metric?.overall_mean
        } (variance = ${metric?.percentage_difference}%).`
      : `Deterministic mathematical evaluation computed across features: ${(
          columns || []
        ).join(', ')}.`);

  // Structured key-value technical metrics
  const technicalEntries = Object.entries({
    ...metric,
    score: discovery_score ? `${discovery_score} / 100` : undefined,
  }).filter(([_, v]) => v !== undefined && typeof v !== 'object');

  const rawJsonPayload = JSON.stringify(
    {
      finding_id: id,
      type,
      title,
      columns,
      metric,
      statistical_evidence: evidence,
      discovery_score,
    },
    null,
    2
  );

  const handleCopyJson = () => {
    navigator.clipboard.writeText(rawJsonPayload);
    setHasCopied(true);
    setTimeout(() => setHasCopied(false), 2000);
  };

  return (
    <div className="w-full rounded-xl border border-zinc-200 bg-white p-5 sm:p-6 shadow-xs hover:border-zinc-300 transition-all">
      {/* Top Bar: Badge, Order, and Columns */}
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <div className="flex items-center space-x-2">
          <span
            className={`inline-flex items-center space-x-1 rounded-md px-2 py-0.5 text-xs font-semibold tracking-wide border ${typeConfig.bg}`}
          >
            <TypeIcon className="h-3 w-3 mr-0.5" />
            <span>
              #{orderNumber} {typeConfig.label}
            </span>
          </span>

          {importance && (
            <span
              className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${
                importance === 'high'
                  ? 'bg-rose-50 text-rose-700 border border-rose-200 font-semibold'
                  : 'bg-zinc-100 text-zinc-600'
              }`}
            >
              {importance.toUpperCase()} PRIORITY
            </span>
          )}
        </div>

        {/* Column pills */}
        {columns && columns.length > 0 && (
          <div className="flex flex-wrap items-center gap-1 font-mono text-xs text-zinc-600">
            {columns.map((c, i) => (
              <React.Fragment key={c}>
                <span className="rounded bg-zinc-100 px-1.5 py-0.5 text-zinc-700">
                  {c}
                </span>
                {i < columns.length - 1 && (
                  <span className="text-zinc-400">↔</span>
                )}
              </React.Fragment>
            ))}
          </div>
        )}
      </div>

      {/* Finding Title */}
      <h3 className="text-base sm:text-lg font-semibold text-zinc-950 tracking-tight leading-snug">
        {title}
      </h3>

      {/* Optional Compact Visual Cue */}
      <VisualCallout finding={finding} />

      {/* Key Metric Highlights Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 my-3.5 bg-zinc-50/80 rounded-lg p-3 border border-zinc-100">
        {type === 'correlation' && (
          <>
            <div>
              <p className="text-[11px] text-zinc-500">Correlation (r)</p>
              <p className="text-sm font-semibold font-mono text-indigo-700">
                {metric.correlation !== undefined ? metric.correlation : 'N/A'}
              </p>
            </div>
            <div>
              <p className="text-[11px] text-zinc-500">Direction</p>
              <p className="text-sm font-semibold text-zinc-800">
                {metric.direction || 'Positive'}
              </p>
            </div>
            <div>
              <p className="text-[11px] text-zinc-500">Strength</p>
              <p className="text-sm font-semibold text-zinc-800">
                {metric.strength || 'Strong'}
              </p>
            </div>
            <div>
              <p className="text-[11px] text-zinc-500">Sample Size</p>
              <p className="text-sm font-semibold font-mono text-zinc-800">
                {metric.sample_size
                  ? Number(metric.sample_size).toLocaleString()
                  : '—'}
              </p>
            </div>
          </>
        )}

        {type === 'group_difference' && (
          <>
            <div>
              <p className="text-[11px] text-zinc-500">Subgroup</p>
              <p className="text-sm font-semibold text-indigo-900 truncate">
                {metric.group ?? 'N/A'}
              </p>
            </div>
            <div>
              <p className="text-[11px] text-zinc-500">Group Average</p>
              <p className="text-sm font-semibold font-mono text-zinc-800">
                {metric.group_mean ?? '—'}
              </p>
            </div>
            <div>
              <p className="text-[11px] text-zinc-500">Overall Mean</p>
              <p className="text-sm font-semibold font-mono text-zinc-800">
                {metric.overall_mean ?? '—'}
              </p>
            </div>
            <div>
              <p className="text-[11px] text-zinc-500">Variance Delta</p>
              <p className="text-sm font-semibold font-mono text-emerald-700">
                {metric.percentage_difference !== undefined
                  ? `${metric.percentage_difference > 0 ? '+' : ''}${metric.percentage_difference}%`
                  : '—'}
              </p>
            </div>
          </>
        )}

        {type === 'time_pattern' && (
          <>
            <div>
              <p className="text-[11px] text-zinc-500">Temporal Dimension</p>
              <p className="text-sm font-semibold text-zinc-800 capitalize">
                {metric.temporal_unit || 'Time'}
              </p>
            </div>
            <div>
              <p className="text-[11px] text-zinc-500">Peak Segment</p>
              <p className="text-sm font-semibold text-emerald-700">
                {metric.peak_segment} ({metric.peak_mean})
              </p>
            </div>
            <div>
              <p className="text-[11px] text-zinc-500">Trough Segment</p>
              <p className="text-sm font-semibold text-zinc-700">
                {metric.trough_segment} ({metric.trough_mean})
              </p>
            </div>
            <div>
              <p className="text-[11px] text-zinc-500">Cycle Spread</p>
              <p className="text-sm font-semibold font-mono text-indigo-700">
                +{metric.spread_percentage}%
              </p>
            </div>
          </>
        )}

        {type === 'interaction' && (
          <>
            <div className="col-span-2">
              <p className="text-[11px] text-zinc-500">Interacting Factors</p>
              <p className="text-sm font-semibold text-zinc-800">
                {(columns || []).slice(0, 2).join(' × ')}
              </p>
            </div>
            <div>
              <p className="text-[11px] text-zinc-500">Effect Ratio</p>
              <p className="text-sm font-semibold font-mono text-indigo-700">
                {metric.interaction_effect_ratio ?? '—'}
              </p>
            </div>
            <div>
              <p className="text-[11px] text-zinc-500">Max Deviation</p>
              <p className="text-sm font-semibold font-mono text-zinc-800">
                {metric.max_deviation ?? '—'}
              </p>
            </div>
          </>
        )}

        {type === 'data_quality' && (
          <>
            <div className="col-span-2">
              <p className="text-[11px] text-zinc-500">Audited Feature</p>
              <p className="text-sm font-semibold text-zinc-800 font-mono">
                {(columns || []).join(', ')}
              </p>
            </div>
            <div className="col-span-2">
              <p className="text-[11px] text-zinc-500">Audit Diagnosis</p>
              <p className="text-sm font-semibold text-amber-700">
                {metric.missing_percentage
                  ? `${metric.missing_percentage}% Missing Rows`
                  : metric.is_exact_duplicate
                  ? '100% Identical Column'
                  : metric.unique_count === 1
                  ? 'Constant Feature (Zero Variance)'
                  : metric.outlier_count
                  ? `${metric.outlier_count} Extreme Outliers (${metric.outlier_percentage}%)`
                  : 'Data Integrity Alert'}
              </p>
            </div>
          </>
        )}

        {type === 'category_numeric' && (
          <>
            <div>
              <p className="text-[11px] text-zinc-500">Max Spread</p>
              <p className="text-sm font-semibold font-mono text-indigo-700">
                {metric.spread ?? '—'}
              </p>
            </div>
            <div>
              <p className="text-[11px] text-zinc-500">Spread Ratio</p>
              <p className="text-sm font-semibold font-mono text-zinc-800">
                {metric.relative_spread_ratio ?? '—'}σ
              </p>
            </div>
            <div className="col-span-2">
              <p className="text-[11px] text-zinc-500">Evaluated Groups</p>
              <p className="text-sm font-semibold text-zinc-800">
                {metric.groups_evaluated ?? '—'} categories
              </p>
            </div>
          </>
        )}
      </div>

      {/* CORE TRUST ARCHITECTURE: AI Interpretation vs Calculated Evidence */}
      <div className="space-y-2.5 my-3">
        {/* Box 1: AI Interpretation */}
        <div className="rounded-lg border border-indigo-100 bg-indigo-50/40 p-3 sm:p-3.5">
          <div className="flex items-center space-x-1.5 text-xs font-semibold text-indigo-900 mb-1">
            <Sparkles className="h-3.5 w-3.5 text-indigo-600" />
            <span>Explained by AI</span>
          </div>
          <p className="text-xs sm:text-sm text-zinc-800 leading-relaxed font-normal">
            {explanation}
          </p>
        </div>

        {/* Box 2: Calculated Statistical Evidence */}
        <div className="rounded-lg border border-zinc-200 bg-zinc-50/70 p-3 sm:p-3.5">
          <div className="flex items-center space-x-1.5 text-xs font-semibold text-zinc-800 mb-1">
            <Calculator className="h-3.5 w-3.5 text-zinc-600" />
            <span>Calculated by DataPilot</span>
            <span className="text-[10px] text-zinc-500 font-normal font-mono">
              (Python / Pandas)
            </span>
          </div>
          <p className="text-xs text-zinc-700 leading-relaxed font-mono">
            {pythonEvidenceText}
          </p>
        </div>

        {/* Box 3: Caution (if present) */}
        {caution && (
          <div className="rounded-lg border border-amber-200/90 bg-amber-50/60 p-3">
            <div className="flex items-center space-x-1.5 text-xs font-semibold text-amber-900 mb-0.5">
              <ShieldAlert className="h-3.5 w-3.5 text-amber-600" />
              <span>Analytical Caution</span>
            </div>
            <p className="text-xs text-amber-800/90 leading-relaxed">
              {caution}
            </p>
          </div>
        )}
      </div>

      {/* Technical Evidence Expansion Drawer */}
      <div className="pt-2 border-t border-zinc-100 mt-3">
        <button
          onClick={() => setIsEvidenceExpanded(!isEvidenceExpanded)}
          className="inline-flex items-center space-x-1.5 text-xs font-medium text-zinc-600 hover:text-zinc-950 transition-colors cursor-pointer py-1"
        >
          {isEvidenceExpanded ? (
            <ChevronUp className="h-3.5 w-3.5" />
          ) : (
            <ChevronDown className="h-3.5 w-3.5" />
          )}
          <span>
            {isEvidenceExpanded ? 'Hide Technical Evidence' : 'Show Technical Evidence'}
          </span>
        </button>

        {isEvidenceExpanded && (
          <div className="mt-3 rounded-lg border border-zinc-200 bg-zinc-900 text-zinc-100 p-4 font-mono text-xs">
            <div className="flex items-center justify-between pb-2 mb-3 border-b border-zinc-800">
              <div className="flex items-center space-x-2 text-[11px] text-zinc-400">
                <Code2 className="h-3.5 w-3.5 text-indigo-400" />
                <span>Deterministic Evidence Schema • ID: {id}</span>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setShowRawJson(!showRawJson)}
                  className="text-[11px] text-zinc-400 hover:text-white underline cursor-pointer"
                >
                  {showRawJson ? 'Structured View' : 'Raw JSON'}
                </button>
                <button
                  onClick={handleCopyJson}
                  className="inline-flex items-center space-x-1 text-[11px] text-zinc-400 hover:text-white cursor-pointer ml-2"
                  title="Copy payload"
                >
                  {hasCopied ? (
                    <Check className="h-3 w-3 text-emerald-400" />
                  ) : (
                    <Copy className="h-3 w-3" />
                  )}
                  <span>{hasCopied ? 'Copied' : 'Copy'}</span>
                </button>
              </div>
            </div>

            {showRawJson ? (
              <pre className="overflow-x-auto text-[11px] text-zinc-300 max-h-60 leading-relaxed">
                {rawJsonPayload}
              </pre>
            ) : (
              <div className="space-y-1.5 text-[11px]">
                {technicalEntries.map(([k, v]) => (
                  <div key={k} className="flex flex-wrap justify-between gap-2 py-0.5 border-b border-zinc-800/60">
                    <span className="text-zinc-400">{k}:</span>
                    <span className="text-indigo-300 font-semibold">{String(v)}</span>
                  </div>
                ))}
                {evidence && typeof evidence === 'object' && (
                  <div className="pt-2">
                    <span className="text-zinc-400 block mb-1">evidence_details:</span>
                    <pre className="bg-zinc-950/80 p-2 rounded text-[10px] text-zinc-300 overflow-x-auto">
                      {JSON.stringify(evidence, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
