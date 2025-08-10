const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export type AnnotateResponse = {
  success: boolean;
  annotated: string[];
  failed: string[];
  error?: string;
};

export async function annotateFrames(sessionId: string, frames: string[], annotation: object): Promise<AnnotateResponse> {
  const res = await fetch(`${API_BASE_URL}/api/annotate/${sessionId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ frames, annotation }),
  });
  return await res.json();
}
