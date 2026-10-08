import React, { useEffect, useState } from 'react';
import { Check, Circle } from 'lucide-react';

interface Stage {
  id: string;
  label: string;
  detail: string;
}

const DISCOVERY_STAGES: Stage[] = [
  {
    id: 'structure',
    label: 'Dataset structure',
    detail: 'Classifying numeric, categorical, and temporal variables',
  },
  {
    id: 'correlations',
    label: 'Numerical relationships',
    detail: 'Evaluating Pearson coefficients and significance across feature pairs',
  },
  {
    id: 'groups',
    label: 'Group differences',
    detail: 'Testing category subgroup deviations from population baseline',
  },
  {
    id: 'time',
    label: 'Time patterns',
    detail: 'Scanning cyclical distributions across temporal units',
  },
  {
    id: 'interactions',
    label: 'Interactions',
    detail: 'Detecting non-additive combinatorial effects across factors',
  },
  {
    id: 'quality',
    label: 'Data quality',
    detail: 'Auditing missingness, constant columns, and statistical anomalies',
  },
  {
    id: 'synthesis',
    label: 'AI synthesis',
    detail: 'Ranking findings and synthesizing analytical explanations',
  },
];

export const DiscoveryProgress: React.FC = () => {
  const [currentStageIndex, setCurrentStageIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStageIndex((prev) => {
        if (prev < DISCOVERY_STAGES.length - 1) {
          return prev + 1;
        }
        return prev;
      });
    }, 650);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="w-full max-w-lg mx-auto rounded-xl border border-zinc-200 bg-white p-6 sm:p-7 shadow-2xs">
      <div className="text-center pb-5 mb-5 border-b border-zinc-100">
        <div className="inline-block text-[11px] font-mono uppercase tracking-widest text-zinc-500 bg-zinc-100 px-2 py-0.5 rounded mb-2">
          Investigation in Progress
        </div>
        <h3 className="text-base sm:text-lg font-semibold text-zinc-950 tracking-tight">
          DataPilot is investigating
        </h3>
        <p className="text-xs text-zinc-500 mt-0.5">
          Evaluating statistical relationships across all variables
        </p>
      </div>

      {/* Stage Checklist */}
      <div className="space-y-2.5 max-w-sm mx-auto">
        {DISCOVERY_STAGES.map((stage, idx) => {
          const isDone = idx < currentStageIndex;
          const isCurrent = idx === currentStageIndex;
          const isPending = idx > currentStageIndex;

          return (
            <div
              key={stage.id}
              className={`flex items-center space-x-3 text-xs transition-opacity duration-200 ${
                isPending ? 'opacity-35' : 'opacity-100'
              }`}
            >
              <div className="shrink-0">
                {isDone ? (
                  <span className="flex h-4.5 w-4.5 items-center justify-center rounded-full bg-emerald-50 text-emerald-600 border border-emerald-200">
                    <Check className="h-2.5 w-2.5 stroke-[2.5]" />
                  </span>
                ) : isCurrent ? (
                  <span className="flex h-4.5 w-4.5 items-center justify-center">
                    <span className="h-2 w-2 rounded-full bg-indigo-600 animate-ping" />
                  </span>
                ) : (
                  <span className="flex h-4.5 w-4.5 items-center justify-center text-zinc-300">
                    <Circle className="h-2 w-2" />
                  </span>
                )}
              </div>

              <div className="flex-1 min-w-0 flex items-baseline justify-between gap-2">
                <span
                  className={`font-medium ${
                    isDone
                      ? 'text-zinc-700'
                      : isCurrent
                      ? 'text-zinc-950 font-semibold'
                      : 'text-zinc-400'
                  }`}
                >
                  {stage.label}
                </span>

                {isCurrent && (
                  <span className="text-[10px] text-indigo-600 font-mono animate-pulse">
                    testing...
                  </span>
                )}
                {isDone && (
                  <span className="text-[10px] text-zinc-400 font-mono">
                    done
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
