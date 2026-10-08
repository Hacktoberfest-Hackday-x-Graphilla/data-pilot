import type { DiscoveryFinding } from '../api/types';

interface VisualCalloutProps {
  finding: DiscoveryFinding;
}

export const VisualCallout: React.FC<VisualCalloutProps> = ({ finding }) => {
  const { type, metric } = finding;

  if (type === 'correlation' && typeof metric.correlation === 'number') {
    const r = metric.correlation;
    // Map r (-1 to 1) to percentage (0% to 100%)
    const pct = Math.max(0, Math.min(100, ((r + 1) / 2) * 100));

    return (
      <div className="rounded border border-zinc-200/80 bg-zinc-50/70 p-2.5 my-2">
        <div className="flex justify-between items-center text-[10px] text-zinc-500 mb-1 font-mono">
          <span>-1.0 (Inverse)</span>
          <span className="text-zinc-700">0.0 (Zero)</span>
          <span>+1.0 (Direct)</span>
        </div>
        <div className="relative h-1.5 w-full rounded-full bg-zinc-200 overflow-visible">
          <div className="absolute top-0 bottom-0 left-1/2 w-0.5 bg-zinc-400" />
          <div
            className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 h-3 w-3 rounded-full bg-zinc-950 border-2 border-white shadow-2xs"
            style={{ left: `${pct}%` }}
          />
        </div>
        <div className="flex justify-between items-center text-[10px] mt-1 font-mono text-zinc-500">
          <span>Direction: <strong className="text-zinc-800">{metric.direction || (r > 0 ? 'Positive' : 'Negative')}</strong></span>
          <span className="font-semibold text-zinc-900">r = {r.toFixed(2)}</span>
        </div>
      </div>
    );
  }

  if (type === 'group_difference' && metric.group_mean !== undefined && metric.overall_mean !== undefined) {
    const grpMean = Number(metric.group_mean);
    const overallMean = Number(metric.overall_mean);
    const maxVal = Math.max(grpMean, overallMean) * 1.15 || 1;
    const grpWidth = Math.max(5, Math.min(100, (grpMean / maxVal) * 100));
    const overallWidth = Math.max(5, Math.min(100, (overallMean / maxVal) * 100));
    const pctDiff = metric.percentage_difference;

    return (
      <div className="rounded border border-zinc-200/80 bg-zinc-50/70 p-2.5 my-2 space-y-1.5">
        <div className="text-[10px] font-mono text-zinc-500 flex justify-between">
          <span>Subgroup comparison</span>
          {pctDiff !== undefined && (
            <span className={`font-semibold ${pctDiff > 0 ? 'text-emerald-700' : 'text-zinc-700'}`}>
              {pctDiff > 0 ? `+${pctDiff}%` : `${pctDiff}%`} vs population
            </span>
          )}
        </div>
        
        {/* Subgroup Bar */}
        <div>
          <div className="flex justify-between text-[10px] text-zinc-700 mb-0.5">
            <span className="font-medium">{metric.group || 'Target group'}</span>
            <span className="font-mono">{grpMean.toLocaleString()}</span>
          </div>
          <div className="h-1.5 w-full bg-zinc-200 rounded-full overflow-hidden">
            <div className="h-full bg-zinc-900 rounded-full" style={{ width: `${grpWidth}%` }} />
          </div>
        </div>

        {/* Population Bar */}
        <div>
          <div className="flex justify-between text-[10px] text-zinc-500 mb-0.5">
            <span>Overall population</span>
            <span className="font-mono">{overallMean.toLocaleString()}</span>
          </div>
          <div className="h-1.5 w-full bg-zinc-200 rounded-full overflow-hidden">
            <div className="h-full bg-zinc-400 rounded-full" style={{ width: `${overallWidth}%` }} />
          </div>
        </div>
      </div>
    );
  }

  if (type === 'time_pattern' && metric.peak_mean !== undefined && metric.trough_mean !== undefined) {
    const peak = Number(metric.peak_mean);
    const trough = Number(metric.trough_mean);
    const maxVal = peak * 1.15 || 1;
    const peakWidth = Math.min(100, (peak / maxVal) * 100);
    const troughWidth = Math.max(5, Math.min(100, (trough / maxVal) * 100));

    return (
      <div className="rounded border border-zinc-200/80 bg-zinc-50/70 p-2.5 my-2 space-y-1.5">
        <div className="text-[10px] font-mono text-zinc-500 flex justify-between">
          <span>Cycle variance ({metric.temporal_unit || 'Period'})</span>
          {metric.spread_percentage && (
            <span className="font-semibold text-zinc-900">
              +{metric.spread_percentage}% peak delta
            </span>
          )}
        </div>

        <div>
          <div className="flex justify-between text-[10px] text-zinc-800 mb-0.5">
            <span>Peak: {metric.peak_segment}</span>
            <span className="font-mono font-medium">{peak.toLocaleString()}</span>
          </div>
          <div className="h-1.5 w-full bg-zinc-200 rounded-full overflow-hidden">
            <div className="h-full bg-zinc-900 rounded-full" style={{ width: `${peakWidth}%` }} />
          </div>
        </div>

        <div>
          <div className="flex justify-between text-[10px] text-zinc-500 mb-0.5">
            <span>Trough: {metric.trough_segment}</span>
            <span className="font-mono">{trough.toLocaleString()}</span>
          </div>
          <div className="h-1.5 w-full bg-zinc-200 rounded-full overflow-hidden">
            <div className="h-full bg-zinc-400 rounded-full" style={{ width: `${troughWidth}%` }} />
          </div>
        </div>
      </div>
    );
  }

  if (type === 'data_quality' && metric.missing_percentage !== undefined) {
    const nullPct = Number(metric.missing_percentage);
    return (
      <div className="rounded border border-zinc-200/80 bg-zinc-50/70 p-2.5 my-2">
        <div className="flex justify-between text-[10px] text-zinc-600 mb-1 font-mono">
          <span>Missingness ratio</span>
          <span className="font-semibold text-amber-800">{nullPct}% null</span>
        </div>
        <div className="h-1.5 w-full bg-zinc-200 rounded-full overflow-hidden">
          <div className="h-full bg-amber-500 rounded-full" style={{ width: `${nullPct}%` }} />
        </div>
      </div>
    );
  }

  return null;
};
