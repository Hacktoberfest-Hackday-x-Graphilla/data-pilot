import { Compass, RefreshCw, AlertCircle, CheckCircle2 } from 'lucide-react';
import type { HealthResponse } from '../api/types';

interface HeaderProps {
  health: HealthResponse | null;
  healthLoading: boolean;
  onReset?: () => void;
  hasActiveDataset: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  healthLoading,
  onReset,
  hasActiveDataset,
}) => {
  const isHealthy = health?.status === 'healthy' || health?.status === 'online';

  return (
    <header className="sticky top-0 z-30 w-full border-b border-zinc-200 bg-white/95 backdrop-blur-sm">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4 sm:px-6">
        {/* Brand Wordmark */}
        <div className="flex items-center space-x-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-indigo-600 text-white shadow-sm shadow-indigo-200">
            <Compass className="h-4.5 w-4.5" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="font-semibold tracking-tight text-zinc-950 text-base">
              DataPilot
            </span>
            <span className="hidden text-xs text-zinc-400 sm:inline-block">
              /
            </span>
            <span className="hidden text-xs font-normal text-zinc-500 sm:inline-block">
              AI-assisted dataset discovery
            </span>
          </div>
        </div>

        {/* Right side status & action */}
        <div className="flex items-center space-x-3">
          {hasActiveDataset && onReset && (
            <button
              onClick={onReset}
              className="inline-flex items-center space-x-1.5 rounded-md border border-zinc-200 bg-white px-2.5 py-1 text-xs font-medium text-zinc-600 shadow-xs hover:bg-zinc-50 hover:text-zinc-900 transition-colors cursor-pointer"
              title="Upload another dataset"
            >
              <RefreshCw className="h-3 w-3" />
              <span>New Dataset</span>
            </button>
          )}

          {/* Backend Status indicator */}
          <div
            className={`inline-flex items-center space-x-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium border ${
              healthLoading
                ? 'bg-zinc-50 text-zinc-600 border-zinc-200'
                : isHealthy
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                : 'bg-amber-50 text-amber-700 border-amber-200'
            }`}
            title={
              health?.gemini_model
                ? `Backend Model: ${health.gemini_model} (${
                    health.gemini_key_configured ? 'API Key Configured' : 'Offline Fallback'
                  })`
                : 'Backend API Status'
            }
          >
            {healthLoading ? (
              <>
                <span className="h-1.5 w-1.5 rounded-full bg-zinc-400 animate-pulse" />
                <span>Connecting...</span>
              </>
            ) : isHealthy ? (
              <>
                <CheckCircle2 className="h-3 w-3 text-emerald-600" />
                <span className="font-medium">Backend Ready</span>
                {health?.gemini_model && (
                  <span className="hidden md:inline text-[10px] text-emerald-600/80 font-mono">
                    ({health.gemini_model})
                  </span>
                )}
              </>
            ) : (
              <>
                <AlertCircle className="h-3 w-3 text-amber-600" />
                <span>Backend Offline</span>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
