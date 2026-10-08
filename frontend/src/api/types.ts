export type DiscoveryCategory =
  | 'correlation'
  | 'group_difference'
  | 'category_numeric'
  | 'time_pattern'
  | 'interaction'
  | 'data_quality'
  | string;

export type ImportanceLevel = 'high' | 'medium' | 'low' | string;

export interface ColumnProfile {
  name: string;
  dtype: string;
  category: 'numeric' | 'categorical' | 'datetime' | 'boolean' | 'other' | string;
  null_count: number;
  null_percentage: number;
  unique_count: number;
  sample_values: unknown[];
}

export interface ProfileReport {
  dataset_id: string;
  filename: string;
  row_count: number;
  column_count: number;
  memory_mb: number;
  duplicate_rows: number;
  columns: ColumnProfile[];
  numeric_columns: string[];
  categorical_columns: string[];
  sample_rows: Record<string, unknown>[];
}

export interface DatasetSummary {
  dataset_id: string;
  filename: string;
  row_count: number;
  column_count: number;
  columns: string[];
  memory_mb: number;
  created_at: string;
}

export interface DiscoveryFinding {
  id: string;
  type: DiscoveryCategory;
  title: string;
  columns: string[];
  metric: Record<string, any>;
  evidence: Record<string, any>;
  explanation: string;
  caution?: string | null;
  importance: ImportanceLevel;
  discovery_score: number;
}

export interface DiscoverySummary {
  rows: number;
  columns: number;
  candidates_examined: number;
  findings_returned: number;
  execution_time_ms: number;
}

export interface DiscoveryRequest {
  dataset_id: string;
  max_findings?: number;
}

export interface DiscoveryResponse {
  dataset_id: string;
  filename: string;
  summary: DiscoverySummary;
  findings: DiscoveryFinding[];
}

export interface HealthResponse {
  status: string;
  gemini_model?: string;
  gemini_key_configured?: boolean;
  app?: string;
  version?: string;
}

export interface ApiErrorResponse {
  detail?: string | Array<{ msg?: string; loc?: string[] }>;
  message?: string;
}
