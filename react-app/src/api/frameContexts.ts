export type FrameContext = {
  frame_id: string;
  // Add other fields as needed from event.json, annotations, cnn_annotations
  annotations?: Record<string, any>;
  cnn_annotations?: Record<string, any>;
  [key: string]: any;
};

export type FrameContextsResponse = {
  contexts: FrameContext[];
};

export type FrameContextFilter = 'ALL' | 'ANNOTATED' | 'PARTIALLY_ANNOTATED' | 'NOT_ANNOTATED';

export async function getFrameContexts(
  sessionId: string,
  start: string,
  pageSize: number,
  filter: FrameContextFilter = 'ALL'
): Promise<FrameContextsResponse> {
  const params = new URLSearchParams({
    start,
    page_size: pageSize.toString(),
    filter
  });
  const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/frame_contexts/${sessionId}?${params}`);
  if (!res.ok) throw new Error('Failed to fetch frame contexts');
  return await res.json();
}
