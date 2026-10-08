import React from 'react';
import { Compass, RefreshCw } from 'lucide-react';
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
    <header className="sticky top-0 z-30 w-full border-b border-zinc-200/80 bg-white/95 backdrop-blur-xs">
      <div className="mx-auto flex h-13 max-w-6xl items-center justify-between px-4 sm:px-6">
        {/* Brand Wordmark */}
        <div className="flex items-center space-x-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-zinc-950 text-white shadow-2xs">
            <Compass className="h-4 w-4" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="font-semibold tracking-tight text-zinc-950 text-sm">
              DataPilot
            </span>
            <span className="text-zinc-300 text-xs select-none">/</span>
            <span className="text-xs text-zinc-500 font-normal">
              AI-assisted dataset discovery
            </span>
          </div>
        </div>

        {/* Right side status & action */}
        <div className="flex items-center space-x-3 text-xs">
          {hasActiveDataset && onReset && (
            <button
              onClick={onReset}
              className="inline-flex items-center space-x-1.5 rounded-md border border-zinc-200 bg-white px-2.5 py-1 text-xs font-medium text-zinc-600 hover:bg-zinc-50 hover:text-zinc-900 transition-colors cursor-pointer"
              title="Upload another dataset"
            >
              <RefreshCw className="h-3 w-3" />
              <span>Change dataset</span>
            </button>
          )}

          {/* Backend Status indicator */}
          <div
            className="inline-flex items-center space-x-1.5 text-xs text-zinc-500"
            title={
              health?.gemini_model
                ? `Engine: ${health.gemini_model} (${
                    health.gemini_key_configured ? 'Online' : 'Fallback'
                  })`
                : 'Backend API Status'
            }
          >
            {healthLoading ? (
              <span className="flex items-center space-x-1.5 text-zinc-400">
                <span className="h-1.5 w-1.5 rounded-full bg-zinc-400 animate-pulse" />
                <span>Connecting</span>
              </span>
            ) : isHealthy ? (
              <span className="flex items-center space-x-1.5 text-zinc-600">
                <span className="h-2 w-2 rounded-full bg-emerald-500" />
                <span className="font-medium text-zinc-700">Connected</span>
              </span>
            ) : (
              <span className="flex items-center space-x-1.5 text-amber-600">
                <span className="h-2 w-2 rounded-full bg-amber-500" />
                <span>Offline</span>
              </span>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
