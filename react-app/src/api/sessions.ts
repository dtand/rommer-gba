const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export type SessionMetadata = Record<string, any>;
export type SessionInfo = {
  session_id: string;
  metadata: SessionMetadata;
};
export type SessionsResponse = {
  sessions: SessionInfo[];
};

export async function getSessions(): Promise<SessionsResponse> {
  const res = await fetch(`${API_BASE_URL}/api/sessions`);
  return await res.json();
}
