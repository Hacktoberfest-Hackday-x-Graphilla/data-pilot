import React, { useState } from 'react';
import {
  TrendingUp,
  GitCompare,
  Clock,
  Layers,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
} from 'lucide-react';
import type { DiscoveryFinding } from '../api/types';
import { DiscoveryChart } from './DiscoveryChart';

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

  // Category Configuration
  const getTypeBadge = (cat: string) => {
    switch (cat) {
      case 'correlation':
        return {
          label: 'Strong relationship',
          icon: TrendingUp,
          badge: 'bg-zinc-100 text-zinc-800 border-zinc-200',
        };
      case 'group_difference':
        return {
          label: 'Group difference',
          icon: GitCompare,
          badge: 'bg-zinc-100 text-zinc-800 border-zinc-200',
        };
      case 'time_pattern':
        return {
          label: 'Time pattern',
          icon: Clock,
          badge: 'bg-zinc-100 text-zinc-800 border-zinc-200',
        };
      case 'interaction':
        return {
          label: 'Interaction',
          icon: Layers,
          badge: 'bg-zinc-100 text-zinc-800 border-zinc-200',
        };
      case 'data_quality':
      case 'anomaly':
        return {
          label: 'Data quality',
          icon: AlertTriangle,
          badge: 'bg-amber-50 text-amber-900 border-amber-200',
        };
      default:
        return {
          label: cat.replace('_', ' '),
          icon: TrendingUp,
          badge: 'bg-zinc-100 text-zinc-800 border-zinc-200',
        };
    }
  };

  const typeConfig = getTypeBadge(type);
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
        } (delta = ${metric?.percentage_difference}%).`
      : `Deterministic mathematical evaluation computed across features: ${(
          columns || []
        ).join(', ')}.`);

  // Structured key-value technical metrics
  const technicalEntries = Object.entries({
    ...metric,
    discovery_score: discovery_score ? `${discovery_score} / 100` : undefined,
  }).filter(([, v]) => v !== undefined && typeof v !== 'object');

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
    <div className="w-full rounded-xl border border-zinc-200 bg-white p-4 sm:p-5 shadow-2xs hover:border-zinc-300 transition-all">
      {/* Top Meta Line: Type + Columns */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-2">
        <div className="flex items-center space-x-2">
          <span
            className={`inline-flex items-center space-x-1 rounded px-2 py-0.5 text-[11px] font-medium border ${typeConfig.badge}`}
          >
            <TypeIcon className="h-3 w-3 mr-0.5" />
            <span>#{orderNumber} {typeConfig.label}</span>
          </span>

          {importance === 'high' && (
            <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider">
              High priority
            </span>
          )}
        </div>

        {columns && columns.length > 0 && (
          <div className="flex items-center space-x-1 font-mono text-xs text-zinc-500">
            {columns.map((c, i) => (
              <React.Fragment key={c}>
                <span className="bg-zinc-100 rounded px-1.5 py-0.2 text-zinc-800">
                  {c}
                </span>
                {i < columns.length - 1 && <span>↔</span>}
              </React.Fragment>
            ))}
          </div>
        )}
      </div>

      {/* Finding Title */}
      <h3 className="text-sm sm:text-base font-semibold text-zinc-950 tracking-tight">
        {title}
      </h3>

      {/* Primary Metric Callout */}
      <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1 my-2.5 py-1.5 px-3 bg-zinc-50 rounded-md border border-zinc-100 text-xs">
        {type === 'correlation' && (
          <>
            <div>
              <span className="text-zinc-500 text-[11px]">Metric:</span>{' '}
              <strong className="text-zinc-950 font-mono font-semibold text-sm">
                r = {metric.correlation}
              </strong>
            </div>
            <div>
              <span className="text-zinc-500 text-[11px]">Direction:</span>{' '}
              <span className="text-zinc-800 font-medium">
                {metric.direction || 'Positive'}
              </span>
            </div>
            <div>
              <span className="text-zinc-500 text-[11px]">Strength:</span>{' '}
              <span className="text-zinc-800 font-medium">
                {metric.strength || 'Strong'}
              </span>
            </div>
            <div>
              <span className="text-zinc-500 text-[11px]">Sample:</span>{' '}
              <span className="text-zinc-700 font-mono">
                {metric.sample_size
                  ? Number(metric.sample_size).toLocaleString()
                  : '—'}
              </span>
            </div>
          </>
        )}

        {type === 'group_difference' && (
          <>
            <div>
              <span className="text-zinc-500 text-[11px]">Subgroup:</span>{' '}
              <strong className="text-zinc-950 font-semibold">
                {metric.group}
              </strong>
            </div>
            <div>
              <span className="text-zinc-500 text-[11px]">Difference:</span>{' '}
              <strong className="text-emerald-700 font-mono font-semibold text-sm">
                {metric.percentage_difference > 0 ? '+' : ''}
                {metric.percentage_difference}%
              </strong>
            </div>
            <div>
              <span className="text-zinc-500 text-[11px]">Group Avg:</span>{' '}
              <span className="text-zinc-800 font-mono">
                {metric.group_mean}
              </span>
            </div>
            <div>
              <span className="text-zinc-500 text-[11px]">Population Avg:</span>{' '}
              <span className="text-zinc-800 font-mono">
                {metric.overall_mean}
              </span>
            </div>
          </>
        )}

        {type === 'time_pattern' && (
          <>
            <div>
              <span className="text-zinc-500 text-[11px]">Dimension:</span>{' '}
              <strong className="text-zinc-900 font-medium capitalize">
                {metric.temporal_unit || 'Time'}
              </strong>
            </div>
            <div>
              <span className="text-zinc-500 text-[11px]">Peak:</span>{' '}
              <strong className="text-emerald-800 font-medium">
                {metric.peak_segment} ({metric.peak_mean})
              </strong>
            </div>
            <div>
              <span className="text-zinc-500 text-[11px]">Trough:</span>{' '}
              <span className="text-zinc-700">
                {metric.trough_segment} ({metric.trough_mean})
              </span>
            </div>
            <div>
              <span className="text-zinc-500 text-[11px]">Cycle Spread:</span>{' '}
              <span className="text-indigo-700 font-mono font-medium">
                +{metric.spread_percentage}%
              </span>
            </div>
          </>
        )}

        {type === 'interaction' && (
          <>
            <div>
              <span className="text-zinc-500 text-[11px]">Factors:</span>{' '}
              <strong className="text-zinc-900">
                {(columns || []).slice(0, 2).join(' × ')}
              </strong>
            </div>
            <div>
              <span className="text-zinc-500 text-[11px]">Effect Ratio:</span>{' '}
              <strong className="text-indigo-700 font-mono">
                {metric.interaction_effect_ratio}
              </strong>
            </div>
            <div>
              <span className="text-zinc-500 text-[11px]">Deviation:</span>{' '}
              <span className="text-zinc-800 font-mono">
                {metric.max_deviation}
              </span>
            </div>
          </>
        )}

        {type === 'data_quality' && (
          <>
            <div>
              <span className="text-zinc-500 text-[11px]">Audit:</span>{' '}
              <strong className="text-amber-800 font-medium">
                {metric.missing_percentage
                  ? `${metric.missing_percentage}% Missing`
                  : metric.is_exact_duplicate
                  ? '100% Identical Column'
                  : metric.unique_count === 1
                  ? 'Constant Column (0 variance)'
                  : 'Outliers detected'}
              </strong>
            </div>
          </>
        )}

        {type === 'category_numeric' && (
          <>
            <div>
              <span className="text-zinc-500 text-[11px]">Max Spread:</span>{' '}
              <strong className="text-zinc-950 font-mono">
                {metric.spread}
              </strong>
            </div>
            <div>
              <span className="text-zinc-500 text-[11px]">Ratio:</span>{' '}
              <span className="text-zinc-800 font-mono">
                {metric.relative_spread_ratio}σ
              </span>
            </div>
          </>
        )}
      </div>

      {/* Evidence-Based Discovery Chart */}
      <DiscoveryChart spec={finding.visualization} />

      {/* Trust Separation: AI Explanation vs Calculated Evidence */}
      <div className="space-y-2 my-2.5 text-xs">
        {/* Box 1: Explained by AI */}
        <div className="rounded-md border border-zinc-200 bg-white p-3">
          <div className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 mb-1 font-semibold">
            Explained by AI
          </div>
          <p className="text-zinc-800 leading-relaxed">
            {explanation}
          </p>
        </div>

        {/* Box 2: Calculated by DataPilot */}
        <div className="rounded-md border border-zinc-200 bg-zinc-50/70 p-3">
          <div className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 mb-1 font-semibold">
            Calculated by DataPilot (Python / Pandas)
          </div>
          <p className="text-zinc-700 font-mono text-[11px] leading-relaxed">
            {pythonEvidenceText}
          </p>
        </div>

        {/* Caution (if applicable) */}
        {caution && (
          <div className="rounded-md border border-amber-200 bg-amber-50/60 p-2.5 text-xs text-amber-900">
            <span className="font-semibold text-[10px] font-mono uppercase tracking-wider block mb-0.5 text-amber-800">
              Analytical Caution
            </span>
            <p className="text-amber-800/90 text-[11px] leading-relaxed">
              {caution}
            </p>
          </div>
        )}
      </div>

      {/* Technical Evidence Drawer */}
      <div className="pt-2 border-t border-zinc-100 mt-2">
        <button
          onClick={() => setIsEvidenceExpanded(!isEvidenceExpanded)}
          className="inline-flex items-center space-x-1 text-xs font-medium text-zinc-600 hover:text-zinc-950 transition-colors cursor-pointer py-0.5"
        >
          {isEvidenceExpanded ? (
            <ChevronUp className="h-3.5 w-3.5" />
          ) : (
            <ChevronDown className="h-3.5 w-3.5" />
          )}
          <span>
            {isEvidenceExpanded ? 'Hide technical evidence' : 'Show technical evidence'}
          </span>
        </button>

        {isEvidenceExpanded && (
          <div className="mt-2.5 rounded-lg border border-zinc-200 bg-zinc-50 p-3.5 text-xs">
            <div className="flex items-center justify-between pb-2 mb-2.5 border-b border-zinc-200 text-zinc-500 text-[11px] font-mono">
              <span>Finding ID: {id}</span>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setShowRawJson(!showRawJson)}
                  className="hover:text-zinc-900 underline cursor-pointer"
                >
                  {showRawJson ? 'Structured view' : 'Raw result'}
                </button>
                <button
                  onClick={handleCopyJson}
                  className="inline-flex items-center space-x-1 hover:text-zinc-900 cursor-pointer ml-2"
                  title="Copy payload"
                >
                  {hasCopied ? (
                    <Check className="h-3 w-3 text-emerald-600" />
                  ) : (
                    <Copy className="h-3 w-3" />
                  )}
                  <span>{hasCopied ? 'Copied' : 'Copy'}</span>
                </button>
              </div>
            </div>

            {showRawJson ? (
              <pre className="overflow-x-auto text-[11px] text-zinc-800 bg-white p-2.5 rounded border border-zinc-200 font-mono max-h-48 leading-relaxed">
                {rawJsonPayload}
              </pre>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1.5 text-[11px] font-mono">
                {technicalEntries.map(([k, v]) => (
                  <div key={k} className="flex justify-between py-0.5 border-b border-zinc-200/60">
                    <span className="text-zinc-500">{k}:</span>
                    <span className="text-zinc-900 font-semibold">{String(v)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
