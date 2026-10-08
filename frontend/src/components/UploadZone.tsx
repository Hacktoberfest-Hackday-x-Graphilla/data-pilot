import React, { useState, useRef } from 'react';
import { UploadCloud, AlertCircle, FileText } from 'lucide-react';

interface UploadZoneProps {
  onUploadFile: (file: File) => void;
  isUploading: boolean;
  uploadError: string | null;
  onClearError?: () => void;
}

export const UploadZone: React.FC<UploadZoneProps> = ({
  onUploadFile,
  isUploading,
  uploadError,
  onClearError,
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const validateAndUpload = (file: File) => {
    setValidationError(null);
    if (onClearError) onClearError();

    if (!file.name.toLowerCase().endsWith('.csv')) {
      setValidationError('Please upload a valid CSV file (.csv).');
      return;
    }

    const maxSizeBytes = 50 * 1024 * 1024; // 50MB
    if (file.size > maxSizeBytes) {
      setValidationError('File size exceeds the 50MB limit.');
      return;
    }

    if (file.size === 0) {
      setValidationError('The selected file is empty.');
      return;
    }

    onUploadFile(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndUpload(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndUpload(e.target.files[0]);
    }
  };

  const handleTriggerPicker = () => {
    if (fileInputRef.current && !isUploading) {
      fileInputRef.current.value = '';
      fileInputRef.current.click();
    }
  };

  // Generate verified demo CSV dataset for instant live testing
  const handleLoadDemoDataset = () => {
    const rows: string[] = [
      'customer_id,customer_age,region,service_type,time_of_day,waiting_time,purchase_amount,spending_score,transaction_timestamp',
    ];

    const regions = ['East', 'West', 'North', 'South'];
    const services = ['Standard', 'Express', 'VIP'];
    const times = ['Morning', 'Afternoon', 'Evening'];

    for (let i = 1; i <= 160; i++) {
      const age = 19 + ((i * 7) % 52);
      const region = regions[i % regions.length];
      const service = services[i % services.length];
      const time = times[i % times.length];

      // Interaction effect on wait time: Express in Evening takes longer
      let wait = 12 + ((i * 3) % 9);
      if (service === 'Express' && time === 'Evening') {
        wait += 44;
      } else if (service === 'VIP') {
        wait = 4;
      }

      // Strong correlation: Age scales purchase amount
      const basePurchase = 25 + age * 4.6 + ((i * 11) % 15);

      // Group difference: East group has +65% higher spending score
      const spending = region === 'East' ? 186.5 : 112.0;

      const hour = time === 'Morning' ? '09' : time === 'Afternoon' ? '14' : '19';
      const day = String(10 + (i % 15)).padStart(2, '0');
      const timestamp = `2026-03-${day} ${hour}:15:00`;

      rows.push(
        `${i},${age},${region},${service},${time},${wait},${basePurchase.toFixed(
          2
        )},${spending},${timestamp}`
      );
    }

    const csvContent = rows.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const demoFile = new File([blob], 'retail_sales_sample.csv', {
      type: 'text/csv',
    });
    validateAndUpload(demoFile);
  };

  const activeError = validationError || uploadError;

  return (
    <div className="w-full max-w-xl mx-auto py-4 sm:py-8">
      {/* Visual Hierarchy: Header Section */}
      <div className="text-center mb-6">
        <div className="inline-block text-[11px] font-mono uppercase tracking-widest text-zinc-500 bg-zinc-100 px-2 py-0.5 rounded mb-3">
          Dataset Discovery
        </div>
        <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight text-zinc-950">
          Upload a dataset.
          <br />
          <span className="text-zinc-600 font-normal">
            Let DataPilot investigate it.
          </span>
        </h1>
        <p className="mt-3 text-sm text-zinc-600 italic">
          &ldquo;Don&rsquo;t know what question to ask? Start with discovery.&rdquo;
        </p>
      </div>

      {/* Main Upload Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleTriggerPicker}
        className={`relative flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 sm:p-10 text-center transition-all cursor-pointer ${
          isDragOver
            ? 'border-indigo-600 bg-indigo-50/40'
            : 'border-zinc-300 bg-white hover:border-zinc-400 hover:bg-zinc-50/50 shadow-2xs'
        } ${isUploading ? 'pointer-events-none opacity-80' : ''}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,text/csv"
          onChange={handleFileInputChange}
          className="hidden"
          disabled={isUploading}
        />

        <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-zinc-100 text-zinc-600 mb-3.5">
          {isUploading ? (
            <div className="h-5 w-5 border-2 border-zinc-900 border-t-transparent rounded-full animate-spin" />
          ) : (
            <UploadCloud className="h-5 w-5" />
          )}
        </div>

        {isUploading ? (
          <div className="space-y-1">
            <p className="text-sm font-semibold text-zinc-900">
              Uploading & parsing dataset...
            </p>
            <p className="text-xs text-zinc-500 font-mono">
              Validating columns and types
            </p>
          </div>
        ) : (
          <div className="space-y-1.5">
            <p className="text-sm font-semibold text-zinc-950">
              DROP CSV HERE
            </p>
            <p className="text-xs text-zinc-500">
              or <span className="text-indigo-600 font-medium hover:underline">Choose CSV file</span>
            </p>
            <p className="text-[11px] text-zinc-400 pt-1 font-mono">
              CSV files only • Max 50MB
            </p>
          </div>
        )}
      </div>

      {/* Error callout if file invalid or upload rejected */}
      {activeError && (
        <div className="mt-4 flex items-start space-x-2.5 rounded-lg border border-rose-200 bg-rose-50/70 p-3 text-xs text-rose-800">
          <AlertCircle className="h-4 w-4 shrink-0 text-rose-600 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold">Upload rejected</p>
            <p className="mt-0.5 text-rose-700">{activeError}</p>
          </div>
        </div>
      )}

      {/* Secondary Action: Demo Sample */}
      <div className="mt-5 flex flex-col sm:flex-row items-center justify-between gap-3 px-1 text-xs text-zinc-500">
        <div className="flex items-center space-x-1.5">
          <FileText className="h-3.5 w-3.5 text-zinc-400" />
          <span>Statistical evidence • AI explanations</span>
        </div>

        <button
          type="button"
          onClick={handleLoadDemoDataset}
          disabled={isUploading}
          className="inline-flex items-center space-x-1.5 rounded-md border border-zinc-200 bg-white px-2.5 py-1 text-xs font-medium text-zinc-700 hover:bg-zinc-50 hover:text-zinc-900 transition-colors cursor-pointer shadow-2xs"
        >
          <span>Try sample dataset</span>
        </button>
      </div>
    </div>
  );
};
