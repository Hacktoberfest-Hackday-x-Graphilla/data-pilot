import type { ApiErrorResponse } from './types';

// Use Vite proxy by default, or explicit environment variable if supplied
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export class ApiError extends Error {
  status: number;
  data?: unknown;

  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

export async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const headers = new Headers(options.headers || {});
  if (!headers.has('Accept')) {
    headers.set('Accept', 'application/json');
  }

  // Do not set Content-Type if body is FormData (let browser set multipart/form-data with boundary)
  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      headers,
    });
  } catch (error: any) {
    // If relative fetch fails (e.g., dev proxy not running), try fallback to http://localhost:8000 directly
    if (!API_BASE_URL && url.startsWith('/')) {
      try {
        const fallbackUrl = `http://localhost:8000${endpoint}`;
        response = await fetch(fallbackUrl, {
          ...options,
          headers,
        });
      } catch {
        throw new ApiError(
          'Could not connect to DataPilot backend. Ensure the server is running on http://localhost:8000.',
          0,
          error
        );
      }
    } else {
      throw new ApiError(
        'Network error: Unable to reach DataPilot API service.',
        0,
        error
      );
    }
  }

  if (!response.ok) {
    let errorMessage = `Request failed with status ${response.status}`;
    let errorData: unknown = null;

    try {
      const parsed: ApiErrorResponse = await response.json();
      errorData = parsed;
      if (typeof parsed.detail === 'string') {
        errorMessage = parsed.detail;
      } else if (Array.isArray(parsed.detail)) {
        errorMessage = parsed.detail.map((d) => d.msg || JSON.stringify(d)).join(', ');
      } else if (parsed.message) {
        errorMessage = parsed.message;
      }
    } catch {
      errorMessage = response.statusText || errorMessage;
    }

    throw new ApiError(errorMessage, response.status, errorData);
  }

  if (response.status === 204) {
    return null as unknown as T;
  }

  return response.json() as Promise<T>;
}
