const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export type FrameInfo = {
  is_complete?: boolean;
  has_partial_data?: boolean;
  // Add other fields as needed
};
export type FramesResponse = {
  frames: FrameInfo[];
  error?: string;
};

export async function getFrames(sessionId?: string): Promise<FramesResponse> {
  const url = sessionId ? `${API_BASE_URL}/api/frames/${sessionId}` : `${API_BASE_URL}/api/frames`;
  const res = await fetch(url);
  return await res.json();
}
