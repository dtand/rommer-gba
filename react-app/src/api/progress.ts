const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export type ProgressResponse = {
  total: number;
  complete: number;
  partial: number;
};

export async function getProgress(sessionId: string): Promise<ProgressResponse> {
  const res = await fetch(`${API_BASE_URL}/api/progress/${sessionId}`);
  return await res.json();
}
