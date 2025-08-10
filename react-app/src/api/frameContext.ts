const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export type FrameContextResponse = Record<string, any>;

export async function getFrameContext(sessionId: string, frameId: string): Promise<FrameContextResponse> {
  const res = await fetch(`${API_BASE_URL}/api/frame_context/${sessionId}/${frameId}`);
  return await res.json();
}
