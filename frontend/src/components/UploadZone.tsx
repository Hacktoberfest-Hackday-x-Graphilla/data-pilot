import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, Sparkles, AlertCircle, ArrowUpRight } from 'lucide-react';

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

    const lower = file.name.toLowerCase();
    const isCsv = lower.endsWith('.csv');
    const isExcel = lower.endsWith('.xlsx') || lower.endsWith('.xls');

    if (!isCsv && !isExcel) {
      setValidationError('Please upload a valid CSV or Excel file (.csv, .xlsx, .xls).');
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
      const age = 19 + (i * 7) % 52;
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
    const demoFile = new File([blob], 'retail_sales_discovery_sample.csv', {
      type: 'text/csv',
    });
    validateAndUpload(demoFile);
  };

  const activeError = validationError || uploadError;

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* Hero explanation card */}
      <div className="text-center mb-8">
        <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight text-zinc-950">
          Upload a dataset.{' '}
          <span className="text-indigo-600">Let DataPilot investigate it.</span>
        </h1>
        <p className="mt-3 text-sm sm:text-base text-zinc-600 max-w-xl mx-auto leading-relaxed">
          DataPilot automatically discovers relationships, subgroup differences,
          cyclical time patterns, factor interactions, and data quality issues —
          so you don't have to know what question to ask first.
        </p>
      </div>

      {/* Drag & Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleTriggerPicker}
        className={`relative flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 sm:p-12 text-center transition-all cursor-pointer ${
          isDragOver
            ? 'border-indigo-500 bg-indigo-50/50 scale-[1.005]'
            : 'border-zinc-200 bg-white hover:border-zinc-300 hover:bg-zinc-50/60 shadow-xs'
        } ${isUploading ? 'pointer-events-none opacity-80' : ''}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,text/csv,.xlsx,.xls,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel"
          onChange={handleFileInputChange}
          className="hidden"
          disabled={isUploading}
        />

        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-zinc-100 text-zinc-600 mb-4 group-hover:bg-indigo-50 group-hover:text-indigo-600 transition-colors">
          {isUploading ? (
            <div className="h-6 w-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
          ) : (
            <UploadCloud className="h-6 w-6" />
          )}
        </div>

        {isUploading ? (
          <div className="space-y-2">
            <p className="text-sm font-medium text-zinc-900">
              Parsing and validating dataset...
            </p>
            <p className="text-xs text-zinc-500">
              Transferring file to DataPilot backend engine
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            <p className="text-sm font-medium text-zinc-900">
              <span className="text-indigo-600 hover:underline">
                Choose a CSV or Excel file
              </span>{' '}
              or drag and drop here
            </p>
            <p className="text-xs text-zinc-500">
              .CSV or .XLSX files up to 50MB • Statistical analysis performed automatically
            </p>
          </div>
        )}
      </div>

      {/* Error callout if file invalid or upload rejected */}
      {activeError && (
        <div className="mt-4 flex items-start space-x-2.5 rounded-lg border border-red-200 bg-red-50 p-3.5 text-xs text-red-800">
          <AlertCircle className="h-4 w-4 shrink-0 text-red-600 mt-0.5" />
          <div className="flex-1">
            <p className="font-medium">Upload issue</p>
            <p className="mt-0.5 text-red-700">{activeError}</p>
          </div>
        </div>
      )}

      {/* Bottom utility helper: Demo sample */}
      <div className="mt-6 flex flex-col sm:flex-row items-center justify-between gap-3 px-1 text-xs text-zinc-500">
        <div className="flex items-center space-x-1.5">
          <FileText className="h-3.5 w-3.5 text-zinc-400" />
          <span>CSV files • Statistical evidence • AI explanations</span>
        </div>

        <button
          type="button"
          onClick={handleLoadDemoDataset}
          disabled={isUploading}
          className="inline-flex items-center space-x-1.5 text-indigo-600 hover:text-indigo-700 font-medium transition-colors cursor-pointer"
        >
          <Sparkles className="h-3.5 w-3.5 text-indigo-500" />
          <span>Or load demo dataset (retail_sales.csv)</span>
          <ArrowUpRight className="h-3 w-3" />
        </button>
      </div>
    </div>
  );
};
