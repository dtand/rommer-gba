const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export type ApplyFieldsResponse = {
  success: boolean;
  error?: string;
};

export async function applyFields(sessionId: string, frameId: string, updateFields: object): Promise<ApplyFieldsResponse> {
  const res = await fetch(`${API_BASE_URL}/api/apply_fields/${sessionId}/${frameId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updateFields),
  });
  return await res.json();
}
