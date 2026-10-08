import { request } from './client';
import type { DatasetSummary, ProfileReport } from './types';

export async function uploadDataset(file: File): Promise<DatasetSummary> {
  const formData = new FormData();
  formData.append('file', file, file.name);

  return request<DatasetSummary>('/api/v1/datasets/upload', {
    method: 'POST',
    body: formData,
  });
}

export async function getDatasetSummary(datasetId: string): Promise<DatasetSummary> {
  return request<DatasetSummary>(`/api/v1/datasets/${encodeURIComponent(datasetId)}`, {
    method: 'GET',
  });
}

export async function listDatasets(): Promise<DatasetSummary[]> {
  return request<DatasetSummary[]>('/api/v1/datasets', {
    method: 'GET',
  });
}

export async function profileDataset(datasetId: string): Promise<ProfileReport> {
  return request<ProfileReport>(`/api/v1/datasets/${encodeURIComponent(datasetId)}/profile`, {
    method: 'POST',
  });
}

export async function deleteDataset(datasetId: string): Promise<void> {
  return request<void>(`/api/v1/datasets/${encodeURIComponent(datasetId)}`, {
    method: 'DELETE',
  });
}
