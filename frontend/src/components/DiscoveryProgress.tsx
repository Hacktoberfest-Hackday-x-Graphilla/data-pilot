import React, { useEffect, useState } from 'react';
import { CheckCircle2, Loader2, Circle } from 'lucide-react';

interface Stage {
  id: string;
  label: string;
  detail: string;
}

const DISCOVERY_STAGES: Stage[] = [
  {
    id: 'profile',
    label: 'Profiling dataset structure & column types',
    detail: 'Classifying numerical, categorical, and temporal variables',
  },
  {
    id: 'correlations',
    label: 'Testing numerical correlations',
    detail: 'Evaluating Pearson coefficients and significance across variable pairs',
  },
  {
    id: 'groups',
    label: 'Comparing categorical group distributions',
    detail: 'Detecting subgroups that diverge significantly from population averages',
  },
  {
    id: 'time',
    label: 'Checking cyclical time patterns',
    detail: 'Analyzing variations across hours, weekdays, and months',
  },
  {
    id: 'interactions',
    label: 'Scanning for non-additive interactions',
    detail: 'Identifying factor pairs with combinatorial effects on outcomes',
  },
  {
    id: 'quality',
    label: 'Auditing data quality & anomalies',
    detail: 'Screening for missingness, constant columns, and extreme outliers',
  },
  {
    id: 'reasoning',
    label: 'Ranking findings & generating AI explanations',
    detail: 'Synthesizing evidence through DataPilot reasoning layer',
  },
];

export const DiscoveryProgress: React.FC = () => {
  const [currentStageIndex, setCurrentStageIndex] = useState(0);

  useEffect(() => {
    // Advance progress stages at realistic intervals to mirror the backend execution
    const interval = setInterval(() => {
      setCurrentStageIndex((prev) => {
        if (prev < DISCOVERY_STAGES.length - 1) {
          return prev + 1;
        }
        return prev;
      });
    }, 700);

    return () => clearInterval(interval);
  }, []);

  const progressPct = Math.round(
    ((currentStageIndex + 1) / DISCOVERY_STAGES.length) * 100
  );

  return (
    <div className="w-full max-w-xl mx-auto rounded-xl border border-zinc-200 bg-white p-6 sm:p-8 shadow-xs">
      <div className="text-center mb-6">
        <div className="inline-flex items-center space-x-2 text-indigo-600 font-semibold text-base mb-1">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span>Investigating dataset...</span>
        </div>
        <p className="text-xs text-zinc-500">
          DataPilot is running automated statistical discovery algorithms
        </p>
      </div>

      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex justify-between text-xs text-zinc-500 mb-1.5 font-mono">
          <span>Stage {currentStageIndex + 1} of {DISCOVERY_STAGES.length}</span>
          <span>{progressPct}%</span>
        </div>
        <div className="h-2 w-full bg-zinc-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-indigo-600 transition-all duration-500 ease-out"
            style={{ width: `${progressPct}%` }}
          />
        </div>
      </div>

      {/* Staged Checklist */}
      <div className="space-y-3">
        {DISCOVERY_STAGES.map((stage, idx) => {
          const isDone = idx < currentStageIndex;
          const isCurrent = idx === currentStageIndex;
          const isPending = idx > currentStageIndex;

          return (
            <div
              key={stage.id}
              className={`flex items-start space-x-3 text-xs transition-opacity duration-300 ${
                isPending ? 'opacity-40' : 'opacity-100'
              }`}
            >
              <div className="mt-0.5 shrink-0">
                {isDone ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                ) : isCurrent ? (
                  <Loader2 className="h-4 w-4 text-indigo-600 animate-spin" />
                ) : (
                  <Circle className="h-4 w-4 text-zinc-300" />
                )}
              </div>

              <div className="flex-1 min-w-0">
                <p
                  className={`font-medium ${
                    isDone
                      ? 'text-zinc-700'
                      : isCurrent
                      ? 'text-indigo-950 font-semibold'
                      : 'text-zinc-400'
                  }`}
                >
                  {stage.label}
                </p>
                {isCurrent && (
                  <p className="text-[11px] text-zinc-500 mt-0.5 animate-pulse">
                    {stage.detail}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
