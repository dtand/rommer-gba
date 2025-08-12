// Aggregate fields API client for /api/aggregate/all/<session_id>

export interface AggregateFieldsResponse {
  contexts: string[];
  scenes: string[];
  tags: string[];
  actions: string[];
  intents: string[];
  outcomes: string[];
}

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

/**
 * Fetches distinct contexts, scenes, tags, actions, intents, and outcomes for a session.
 * @param sessionId - The session ID to aggregate fields for.
 * @returns Promise with aggregate fields response
 */
export async function fetchAggregateFields(sessionId: string): Promise<AggregateFieldsResponse> {
  const url = `${BASE_URL}/api/aggregate/all/${sessionId}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch aggregate fields: ${response.status}`);
  }
  return response.json();
}
