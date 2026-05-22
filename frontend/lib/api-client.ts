import type {
  AgentRunResult,
  Company,
  Property,
  RiskAssessment,
  Scenario,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${path}: ${text}`);
  }
  return res.json() as Promise<T>;
}

// ─────────────────────────── Companies ───────────────────────────────────────
export const api = {
  companies: {
    list: () => request<Company[]>("/api/v1/companies"),
    get: (id: string) => request<Company>(`/api/v1/companies/${id}`),
    create: (body: Omit<Company, "company_id">) =>
      request<Company>("/api/v1/companies", { method: "POST", body: JSON.stringify(body) }),
  },

  // ─────────────────────────── Properties ──────────────────────────────────
  properties: {
    list: (companyId?: string) =>
      request<Property[]>(`/api/v1/properties${companyId ? `?company_id=${companyId}` : ""}`),
    get: (id: string) => request<Property>(`/api/v1/properties/${id}`),
    create: (body: Omit<Property, "property_id">) =>
      request<Property>("/api/v1/properties", { method: "POST", body: JSON.stringify(body) }),
  },

  // ─────────────────────────── Assessments ─────────────────────────────────
  assessments: {
    run: (params: {
      company_id: string;
      property_ids: string[];
      scenario?: Scenario;
      time_horizon?: number;
    }) =>
      request<{ assessments: RiskAssessment[]; count: number }>("/api/v1/assessments/run", {
        method: "POST",
        body: JSON.stringify(params),
      }),
    get: (id: string) => request<RiskAssessment>(`/api/v1/assessments/${id}`),
    list: (params?: { property_id?: string; company_id?: string }) => {
      const qs = new URLSearchParams(params as Record<string, string>).toString();
      return request<RiskAssessment[]>(`/api/v1/assessments${qs ? `?${qs}` : ""}`);
    },
  },

  // ─────────────────────────── Agent runs ──────────────────────────────────
  agents: {
    run: (params: {
      company_id: string;
      property_ids: string[];
      scenario?: Scenario;
      year?: number;
      task_type?: string;
    }) =>
      request<AgentRunResult>("/api/v1/agents/run", {
        method: "POST",
        body: JSON.stringify(params),
      }),
    get: (runId: string) => request<AgentRunResult>(`/api/v1/agents/${runId}`),
    submitFeedback: (runId: string, feedback: string, approved: boolean) =>
      request(`/api/v1/agents/${runId}/feedback`, {
        method: "POST",
        body: JSON.stringify({ feedback, approved }),
      }),
  },

  // ─────────────────────────── Disclosures ─────────────────────────────────
  disclosures: {
    generate: (params: {
      company_id: string;
      property_ids: string[];
      scenario?: Scenario;
      year?: number;
    }) =>
      request<{ run_id: string; disclosure_markdown: string; confidence: number }>(
        "/api/v1/disclosures/generate",
        { method: "POST", body: JSON.stringify(params) }
      ),
    get: (runId: string) =>
      request<{ run_id: string; disclosure_markdown: string; approval_state: string }>(
        `/api/v1/disclosures/${runId}`
      ),
  },
};
