import { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { UploadZone } from './components/UploadZone';
import { DatasetOverview } from './components/DatasetOverview';
import { DiscoveryCTA } from './components/DiscoveryCTA';
import { DiscoveryProgress } from './components/DiscoveryProgress';
import { DiscoveryReportView } from './components/DiscoveryReportView';
import { ErrorState } from './components/ErrorState';
import { uploadDataset, profileDataset } from './api/datasets';
import { discoverPatterns, checkHealth } from './api/discovery';
import {
  DatasetSummary,
  ProfileReport,
  DiscoveryResponse,
  HealthResponse,
} from './api/types';

type AppStep = 'idle' | 'uploading' | 'ready' | 'discovering' | 'complete' | 'error';

export function App() {
  const [step, setStep] = useState<AppStep>('idle');
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState(true);

  // Active dataset state
  const [dataset, setDataset] = useState<DatasetSummary | null>(null);
  const [profile, setProfile] = useState<ProfileReport | null>(null);
  const [isLoadingProfile, setIsLoadingProfile] = useState(false);

  // Discovery state
  const [maxFindings, setMaxFindings] = useState<number>(5);
  const [discoveryReport, setDiscoveryReport] = useState<DiscoveryResponse | null>(null);

  // Errors
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [generalError, setGeneralError] = useState<string | null>(null);

  // Check backend health on initial load
  useEffect(() => {
    let isMounted = true;
    checkHealth()
      .then((data) => {
        if (isMounted) {
          setHealth(data);
          setHealthLoading(false);
        }
      })
      .catch(() => {
        if (isMounted) {
          setHealth(null);
          setHealthLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  // Upload handler
  const handleUploadFile = async (file: File) => {
    setUploadError(null);
    setGeneralError(null);
    setStep('uploading');

    try {
      const summary = await uploadDataset(file);
      setDataset(summary);
      setStep('ready');

      // Fetch profile asynchronously in background to enrich overview
      setIsLoadingProfile(true);
      profileDataset(summary.dataset_id)
        .then((prof) => {
          setProfile(prof);
          setIsLoadingProfile(false);
        })
        .catch(() => {
          setIsLoadingProfile(false);
        });
    } catch (err: any) {
      setStep('idle');
      setUploadError(
        err.message ||
          'Failed to parse or upload the CSV file. Please ensure it is a valid format.'
      );
    }
  };

  // Discovery action handler
  const handleDiscover = async (count: number) => {
    if (!dataset) return;

    setGeneralError(null);
    setStep('discovering');

    try {
      const report = await discoverPatterns(dataset.dataset_id, count);
      setDiscoveryReport(report);
      setStep('complete');
    } catch (err: any) {
      setStep('error');
      setGeneralError(
        err.message ||
          "DataPilot couldn't analyze this dataset. The backend analysis service may be unavailable or experienced an error."
      );
    }
  };

  // Reset to initial upload state
  const handleReset = () => {
    setDataset(null);
    setProfile(null);
    setDiscoveryReport(null);
    setUploadError(null);
    setGeneralError(null);
    setStep('idle');
  };

  return (
    <div className="min-h-screen flex flex-col bg-zinc-50 text-zinc-900 font-sans">
      <Header
        health={health}
        healthLoading={healthLoading}
        hasActiveDataset={!!dataset}
        onReset={handleReset}
      />

      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 py-8 sm:py-12">
        {/* Step: IDLE (Upload zone) */}
        {step === 'idle' && (
          <UploadZone
            onUploadFile={handleUploadFile}
            isUploading={false}
            uploadError={uploadError}
            onClearError={() => setUploadError(null)}
          />
        )}

        {/* Step: UPLOADING */}
        {step === 'uploading' && (
          <UploadZone
            onUploadFile={handleUploadFile}
            isUploading={true}
            uploadError={null}
          />
        )}

        {/* Step: READY (Dataset Loaded, CTA to discover) */}
        {step === 'ready' && dataset && (
          <div className="space-y-6">
            <DatasetOverview
              dataset={dataset}
              profile={profile}
              isLoadingProfile={isLoadingProfile}
              onRemoveDataset={handleReset}
            />

            <DiscoveryCTA
              onDiscover={handleDiscover}
              isDiscovering={false}
              maxFindings={maxFindings}
              onMaxFindingsChange={setMaxFindings}
            />
          </div>
        )}

        {/* Step: DISCOVERING (Staged progress) */}
        {step === 'discovering' && dataset && (
          <div className="space-y-6">
            <DatasetOverview
              dataset={dataset}
              profile={profile}
              isLoadingProfile={false}
              onRemoveDataset={handleReset}
            />

            <DiscoveryProgress />
          </div>
        )}

        {/* Step: COMPLETE (Discovery report & cards) */}
        {step === 'complete' && discoveryReport && (
          <div className="space-y-6">
            {dataset && (
              <DatasetOverview
                dataset={dataset}
                profile={profile}
                isLoadingProfile={false}
                onRemoveDataset={handleReset}
              />
            )}

            <DiscoveryReportView
              report={discoveryReport}
              onRunAgain={() => handleDiscover(maxFindings)}
              onReset={handleReset}
            />
          </div>
        )}

        {/* Step: ERROR */}
        {step === 'error' && (
          <div className="space-y-6">
            {dataset && (
              <DatasetOverview
                dataset={dataset}
                profile={profile}
                isLoadingProfile={false}
                onRemoveDataset={handleReset}
              />
            )}

            <ErrorState
              message={
                generalError ||
                'An unexpected error occurred while communicating with DataPilot.'
              }
              onRetry={() => handleDiscover(maxFindings)}
              onReset={handleReset}
            />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="w-full border-t border-zinc-200 py-6 text-center text-xs text-zinc-400 bg-white">
        <div className="max-w-5xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>DataPilot — Questionless AI Dataset Discovery Engine</span>
          <span className="font-mono text-zinc-400">
            Statistical Evidence via Python • Explanations via LLM
          </span>
        </div>
      </footer>
    </div>
  );
}

export default App;
