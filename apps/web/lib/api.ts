import type {
  Analysis,
  AuditEntry,
  CaseEnvelope,
  CaseInput,
  CaseSummary,
  CaseVersionSummary,
  DemoCase,
  Money,
  RuntimeInfo,
} from "./types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

type ApiError = {
  code?: string;
  message?: string;
  remediation?: string;
  request_id?: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    let detail: ApiError = {};
    try {
      detail = (await response.json()) as ApiError;
    } catch {
      /* non-JSON upstream error */
    }
    throw new Error(
      [
        detail.message ?? `Request failed (${response.status})`,
        detail.remediation,
      ]
        .filter(Boolean)
        .join(" "),
    );
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  runtime: () => request<RuntimeInfo>("/runtime"),
  demos: () => request<DemoCase[]>("/demo-cases"),
  demoTemplate: (slug: string) =>
    request<CaseInput>(`/demo-cases/${slug}/template`),
  openDemo: (slug: string) =>
    request<CaseEnvelope>(`/demo-cases/${slug}/open`, { method: "POST" }),
  listCases: () => request<CaseSummary[]>("/cases"),
  getCase: (id: string) => request<CaseEnvelope>(`/cases/${id}`),
  createCase: (input: CaseInput) =>
    request<CaseEnvelope>("/cases", {
      method: "POST",
      body: JSON.stringify(input),
    }),
  validateInput: (input: CaseInput) =>
    request<{
      valid: boolean;
      missing: string[];
      warnings: string[];
      estimated_confidence: number;
    }>("/cases/validate-input", {
      method: "POST",
      body: JSON.stringify(input),
    }),
  updateCase: (id: string, input: CaseInput) =>
    request<CaseEnvelope>(`/cases/${id}`, {
      method: "PUT",
      body: JSON.stringify(input),
    }),
  validate: (id: string) =>
    request<{
      valid: boolean;
      missing: string[];
      warnings: string[];
      estimated_confidence: number;
    }>(`/cases/${id}/validate`, { method: "POST" }),
  analyze: (id: string) =>
    request<Analysis>(`/cases/${id}/analyze`, { method: "POST" }),
  duplicate: (id: string) =>
    request<CaseEnvelope>(`/cases/${id}/duplicate`, { method: "POST" }),
  archive: (id: string) =>
    request<CaseEnvelope>(`/cases/${id}/archive`, { method: "POST" }),
  delete: (id: string) => request<void>(`/cases/${id}`, { method: "DELETE" }),
  versions: (id: string) =>
    request<CaseVersionSummary[]>(`/cases/${id}/versions`),
  restoreVersion: (id: string, version: number) =>
    request<CaseEnvelope>(`/cases/${id}/versions/${version}/restore`, {
      method: "POST",
    }),
  audit: (id: string) => request<AuditEntry[]>(`/cases/${id}/audit`),
};

function grouping(value: bigint, locale: string): string {
  return new Intl.NumberFormat(locale, { maximumFractionDigits: 0 }).format(
    value,
  );
}

export function money(value: Money, locale: string, compact = false): string {
  const minor = BigInt(value.amount_minor);
  const scale = 10n ** BigInt(value.minor_unit_exponent);
  const whole = minor / scale;
  const sign = whole < 0n ? "-" : "";
  const absolute = whole < 0n ? -whole : whole;
  const symbol = value.currency === "USD" ? "$" : `${value.currency} `;
  if (compact) {
    const million = 1_000_000n;
    if (absolute >= million) {
      const tenths = (absolute * 10n + million / 2n) / million;
      return `${sign}${symbol}${tenths / 10n}.${tenths % 10n}M`;
    }
  }
  return `${sign}${symbol}${grouping(absolute, locale)}`;
}

export async function downloadMemo(
  id: string,
  locale: string,
  detailed = false,
): Promise<void> {
  const response = await fetch(
    `${API_URL}/cases/${id}/memo.pdf?locale=${encodeURIComponent(locale)}&detail=${detailed ? "detailed" : "executive"}`,
    { credentials: "include" },
  );
  if (!response.ok) throw new Error("Memo export failed");
  const url = URL.createObjectURL(await response.blob());
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `northstar-credit-memo-${locale}.pdf`;
  anchor.click();
  URL.revokeObjectURL(url);
}
