"use client";

import { History } from "lucide-react";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { AuditEntry, CaseVersionSummary } from "@/lib/types";

export function AuditHistory({
  caseId,
  currentVersion,
  language,
  onRestored,
}: {
  caseId: string;
  currentVersion: number;
  language: "en" | "zh-TW";
  onRestored: () => Promise<void>;
}) {
  const zh = language === "zh-TW";
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [versions, setVersions] = useState<CaseVersionSummary[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState<number | null>(null);
  async function load() {
    try {
      const [audit, versionRows] = await Promise.all([
        api.audit(caseId),
        api.versions(caseId),
      ]);
      setEntries(audit);
      setVersions(versionRows);
      setError("");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    }
  }
  useEffect(() => {
    let cancelled = false;
    void Promise.all([api.audit(caseId), api.versions(caseId)])
      .then(([audit, versionRows]) => {
        if (cancelled) return;
        setEntries(audit);
        setVersions(versionRows);
        setError("");
      })
      .catch((cause: unknown) => {
        if (!cancelled) {
          setError(cause instanceof Error ? cause.message : String(cause));
        }
      });
    return () => {
      cancelled = true;
    };
  }, [caseId]);
  const local = (value: string) =>
    zh
      ? ((
          {
            draft: "草稿",
            stale: "已過期",
            analyzed: "已分析",
            created: "已建立",
            updated: "已更新",
            analyzed_case: "已分析",
            archived: "已封存",
            restored: "已還原",
            duplicated: "已複製",
            version_restored: "已還原版本",
          } as Record<string, string>
        )[value] ?? "案件事件")
      : value;
  const localDate = (value: string) => {
    const explicitZone = /(?:Z|[+-]\d{2}:?\d{2})$/.test(value);
    return new Date(explicitZone ? value : `${value}Z`).toLocaleString(
      zh ? "zh-TW" : "en-US",
    );
  };
  async function restore(version: number) {
    setBusy(version);
    try {
      await api.restoreVersion(caseId, version);
      await onRestored();
      await load();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setBusy(null);
    }
  }
  return (
    <details className="audit-history">
      <summary>
        <History size={16} />
        {zh ? "版本與稽核歷史" : "Version and audit history"}
      </summary>
      <div>
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        <div className="two-column">
          <section>
            <h3>{zh ? "版本" : "Versions"}</h3>
            <ol>
              {versions.map((item) => (
                <li key={item.version}>
                  <strong>v{item.version}</strong> · {local(item.status)} ·{" "}
                  {localDate(item.created_at)}
                  {item.version < currentVersion && (
                    <button
                      type="button"
                      disabled={busy !== null}
                      onClick={() => restore(item.version)}
                    >
                      {busy === item.version
                        ? zh
                          ? "還原中…"
                          : "Restoring…"
                        : zh
                          ? "還原此版本"
                          : "Restore version"}
                    </button>
                  )}
                </li>
              ))}
            </ol>
          </section>
          <section>
            <h3>{zh ? "稽核事件" : "Audit events"}</h3>
            <ol>
              {entries.map((item) => (
                <li key={item.id}>
                  <strong>{local(item.action)}</strong> · v{item.version} ·{" "}
                  {localDate(item.created_at)}
                </li>
              ))}
            </ol>
          </section>
        </div>
        <button className="button secondary" type="button" onClick={load}>
          {zh ? "重新整理歷史" : "Refresh history"}
        </button>
      </div>
    </details>
  );
}
