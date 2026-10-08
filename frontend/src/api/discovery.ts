import { request } from './client';
import { DiscoveryResponse, HealthResponse } from './types';

export async function discoverPatterns(
  datasetId: string,
  maxFindings: number = 5
): Promise<DiscoveryResponse> {
  return request<DiscoveryResponse>('/api/v1/discovery', {
    method: 'POST',
    body: JSON.stringify({
      dataset_id: datasetId,
      max_findings: maxFindings,
    }),
  });
}

export async function checkHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health', {
    method: 'GET',
  });
}
