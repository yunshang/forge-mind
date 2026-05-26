const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface GenerateRequest {
  prompt: string;
}

export interface SessionSummary {
  id: string;
  name: string;
  message_count: number;
  has_result: boolean;
  created_at: string;
  updated_at: string;
}

export interface SessionMessage {
  role: string;
  content: string;
  timestamp: string;
}

export interface Session extends SessionSummary {
  messages: SessionMessage[];
  current_result: GenerateResponse | Record<string, never>;
}

export interface GenerateResponse {
  status: string;
  contract_name: string;
  solidity_code: string;
  constructor_args: string[];
  description: string;
  audit_result: {
    status: string;
    vulnerabilities: Array<{
      severity: string;
      vulnerability: string;
      location: string;
      description: string;
    }>;
  };
  graph_data: {
    nodes: Array<{
      id: string;
      type: string;
      position: { x: number; y: number };
      data: Record<string, unknown>;
    }>;
    edges: Array<{
      id: string;
      source: string;
      target: string;
      type?: string;
      label?: string;
      animated?: boolean;
    }>;
  };
  sandbox_result: {
    status: string;
    contract_address?: string;
    abi?: Array<Record<string, unknown>>;
    functions?: Array<{
      name: string;
      inputs: Array<{ name: string; type: string }>;
      outputs: Array<{ name: string; type: string }>;
      stateMutability: string;
      isRead: boolean;
    }>;
    error?: string;
  };
  logs: Array<{
    agent: string;
    message: string;
    level: string;
  }>;
  iterations: number;
  error: string;
}

export interface SandboxCallRequest {
  contract_address: string;
  abi: Array<Record<string, unknown>>;
  function_name: string;
  args: unknown[];
  is_read: boolean;
  value?: number;
}

export interface SandboxCallResponse {
  status: string;
  result: string;
  transaction_hash: string;
  error: string;
}

export async function generateContract(prompt: string): Promise<GenerateResponse> {
  const res = await fetch(`${API_BASE}/api/contracts/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function callSandboxFunction(data: SandboxCallRequest): Promise<SandboxCallResponse> {
  const res = await fetch(`${API_BASE}/api/sandbox/call`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

// --- Session API ---

export async function createSession(name?: string): Promise<Session> {
  const res = await fetch(`${API_BASE}/api/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: name || "" }),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function listSessions(): Promise<SessionSummary[]> {
  const res = await fetch(`${API_BASE}/api/sessions`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function getSession(sessionId: string): Promise<Session> {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function deleteSession(sessionId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
}

export async function generateInSession(sessionId: string, prompt: string): Promise<GenerateResponse & { session_id: string }> {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export interface VisualizeRequest {
  solidity_code: string;
  contract_name?: string;
}

export interface VisualizeResponse {
  status: string;
  graph_data: {
    nodes: Array<{
      id: string;
      type: string;
      position: { x: number; y: number };
      data: Record<string, unknown>;
    }>;
    edges: Array<{
      id: string;
      source: string;
      target: string;
      type?: string;
      label?: string;
      animated?: boolean;
    }>;
  };
  error?: string;
}

export async function visualizeContract(solidityCode: string, contractName?: string): Promise<VisualizeResponse> {
  const res = await fetch(`${API_BASE}/api/contracts/visualize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ solidity_code: solidityCode, contract_name: contractName || "" }),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export interface EstimateRequest {
  contract_address: string;
  abi: Array<Record<string, unknown>>;
  function_name: string;
  args: unknown[];
  value?: number;
}

export interface EstimateResponse {
  status: string;
  gas_limit: number;
  gas_price: number;
  estimated_cost_wei: number;
  estimated_cost_eth: string;
  error?: string;
}

export async function estimateGas(data: EstimateRequest): Promise<EstimateResponse> {
  const res = await fetch(`${API_BASE}/api/sandbox/estimate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}
