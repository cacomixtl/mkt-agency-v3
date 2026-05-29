/**
 * client.ts — Base API client for the Director's Cockpit.
 *
 * Configures a fetch-based client pointing to VITE_API_BASE_URL.
 * All requests include Content-Type: application/json and the
 * X-Thread-ID header (from localStorage) per BRIDGE_SPEC.md §6.
 */

import type { APIEnvelope, CampaignResumeRequest } from '@/types';

const BASE_URL = import.meta.env.DEV
  ? (import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000')
  : '/api';

function getThreadId(): string | null {
  try {
    return localStorage.getItem('agency_thread_id');
  } catch {
    return null;
  }
}

export function setThreadId(threadId: string): void {
  try {
    localStorage.setItem('agency_thread_id', threadId);
  } catch {
    // SSR or restricted environment — silently ignore
  }
}

function buildHeaders(extra?: Record<string, string>): HeadersInit {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...extra,
  };

  const threadId = getThreadId();
  if (threadId) {
    headers['X-Thread-ID'] = threadId;
  }

  return headers;
}

/**
 * POST request returning a typed APIEnvelope.
 */
export async function post<T = unknown>(
  path: string,
  body: unknown,
): Promise<APIEnvelope<T>> {
  const response = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: buildHeaders(),
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new ApiError(response.status, await response.text());
  }

  return response.json() as Promise<APIEnvelope<T>>;
}

/**
 * GET request returning a typed APIEnvelope.
 */
export async function get<T = unknown>(
  path: string,
): Promise<APIEnvelope<T>> {
  const response = await fetch(`${BASE_URL}${path}`, {
    method: 'GET',
    headers: buildHeaders(),
  });

  if (!response.ok) {
    throw new ApiError(response.status, await response.text());
  }

  return response.json() as Promise<APIEnvelope<T>>;
}

/**
 * Open an SSE stream via EventSource.
 * Returns a native EventSource instance the caller can attach
 * event listeners to. Caller is responsible for closing.
 */
export function stream(path: string): EventSource {
  const url = `${BASE_URL}${path}`;
  return new EventSource(url);
}

/**
 * POST /campaign/{id}/resume — Submit a HITL decision.
 * Wraps the generic post() helper with a typed response shape.
 */
export async function resumeCampaign(
  campaignId: string,
  body: CampaignResumeRequest,
): Promise<APIEnvelope<{ thread_id: string; decision: string; stage?: string }>> {
  return post<{ thread_id: string; decision: string; stage?: string }>(
    `/campaign/${campaignId}/resume`,
    body,
  );
}

/**
 * Structured API error with HTTP status code.
 */
export class ApiError extends Error {
  constructor(
    public readonly statusCode: number,
    public readonly body: string,
  ) {
    super(`API ${statusCode}: ${body}`);
    this.name = 'ApiError';
  }
}

export const api = { get, post, stream, setThreadId, resumeCampaign } as const;
