const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export type MemoryQueryResponse = {
  success: boolean;
  query: string;
  sql_query: string;
  results: any[];
  explanation: string;
  confidence: number;
  execution_time: number;
  result_count: number;
};

export async function queryMemory(query: string): Promise<MemoryQueryResponse> {
  const res = await fetch(`${API_BASE_URL}/memory/api/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });
  return await res.json();
}
