const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

// Returns a PNG image for a frame
export async function getFrameImage(sessionId: string, frameId: string): Promise<Blob> {
  const res = await fetch(`${API_BASE_URL}/api/frame_image/${sessionId}/${frameId}`);
  if (!res.ok) throw new Error('Image not found');
  return await res.blob();
}
