const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export type AggregateFieldResponse = {
  [key: string]: string[];
};

export async function aggregateField(field: string, sessionId: string): Promise<AggregateFieldResponse> {
  const res = await fetch(`${API_BASE_URL}/api/aggregate/${field}/${sessionId}`);
  return await res.json();
}

export type ActionsAggregateResponse = {
  actions: string[];
  intents: string[];
  outcomes: string[];
};

export async function aggregateActions(sessionId: string): Promise<ActionsAggregateResponse> {
  const res = await fetch(`${API_BASE_URL}/api/aggregate/actions/${sessionId}`);
  return await res.json();
}
