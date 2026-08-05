import type { Analysis, CaseEnvelope, CaseInput, DemoCase, Money } from "./types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

export function sessionId(): string {
  if (typeof window === "undefined") return "server-render";
  const key = "northstar-session";
  const current = window.localStorage.getItem(key);
  if (current) return current;
  const created = crypto.randomUUID();
  window.localStorage.setItem(key, created);
  return created;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", "X-Northstar-Session": sessionId(), ...init?.headers },
  });
  if (!response.ok) throw new Error((await response.text()) || `Request failed (${response.status})`);
  return response.json() as Promise<T>;
}

export const api = {
  demos: () => request<DemoCase[]>("/demo-cases"),
  openDemo: (slug: string) => request<CaseEnvelope>(`/demo-cases/${slug}/open`, { method: "POST" }),
  getCase: (id: string) => request<CaseEnvelope>(`/cases/${id}`),
  createCase: (input: CaseInput) => request<CaseEnvelope>("/cases", { method: "POST", body: JSON.stringify(input) }),
  analyze: (id: string) => request<Analysis>(`/cases/${id}/analyze`, { method: "POST" }),
};

export function money(value: Money, locale: string, compact = false): string {
  const amount = value.amount_minor / 10 ** value.minor_unit_exponent;
  return new Intl.NumberFormat(locale, {
    style: "currency", currency: value.currency, maximumFractionDigits: compact ? 1 : 0,
    notation: compact ? "compact" : "standard",
  }).format(amount);
}

export async function downloadMemo(id: string): Promise<void> {
  const response = await fetch(`${API_URL}/cases/${id}/memo.pdf`, { headers: { "X-Northstar-Session": sessionId() } });
  if (!response.ok) throw new Error("Memo export failed");
  const url = URL.createObjectURL(await response.blob());
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "northstar-credit-memo.pdf";
  anchor.click();
  URL.revokeObjectURL(url);
}
