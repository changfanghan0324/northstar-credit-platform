"use client";

import {
  Archive,
  Copy,
  FilePlus2,
  FolderOpen,
  LoaderCircle,
  Search,
  Trash2,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Header } from "./Header";
import { api } from "@/lib/api";
import { type Language, prefix } from "@/lib/i18n";
import type { CaseSummary, RuntimeInfo } from "@/lib/types";

export function Cases({ language }: { language: Language }) {
  const zh = language === "zh-TW";
  const root = prefix(language);
  const [items, setItems] = useState<CaseSummary[]>([]);
  const [runtime, setRuntime] = useState<RuntimeInfo | null>(null);
  const [query, setQuery] = useState("");
  const [showArchived, setShowArchived] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  async function refresh() {
    setLoading(true);
    setError("");
    try {
      const [cases, mode] = await Promise.all([api.listCases(), api.runtime()]);
      setItems(cases);
      setRuntime(mode);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    let active = true;
    Promise.all([api.listCases(), api.runtime()])
      .then(([cases, mode]) => {
        if (active) {
          setItems(cases);
          setRuntime(mode);
        }
      })
      .catch((cause) => {
        if (active)
          setError(cause instanceof Error ? cause.message : String(cause));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);
  const shown = useMemo(
    () =>
      items
        .filter(
          (item) =>
            (showArchived || !item.archived) &&
            `${item.title} ${item.borrower_name} ${item.status}`
              .toLowerCase()
              .includes(query.toLowerCase()),
        )
        .toSorted((a, b) => b.updated_at.localeCompare(a.updated_at)),
    [items, query, showArchived],
  );
  async function act(id: string, action: "duplicate" | "archive" | "delete") {
    if (
      action === "delete" &&
      !window.confirm(
        zh
          ? "永久刪除此案件？此動作無法復原。"
          : "Permanently delete this case? This cannot be undone.",
      )
    )
      return;
    setBusy(id);
    setError("");
    try {
      if (action === "duplicate") await api.duplicate(id);
      if (action === "archive") await api.archive(id);
      if (action === "delete") await api.delete(id);
      await refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setBusy("");
    }
  }
  return (
    <>
      <Header language={language} />
      <main className="cases-page">
        <div className="cases-head">
          <div>
            <h1>{zh ? "授信案件" : "Credit cases"}</h1>
            <p>
              {zh
                ? "搜尋、重新開啟、複製、封存或永久刪除匿名案件。"
                : "Search, reopen, duplicate, archive, or permanently delete anonymous cases."}
            </p>
          </div>
          <Link className="button primary" href={`${root}/app/cases/new`}>
            <FilePlus2 size={17} />
            {zh ? "新增案件" : "New case"}
          </Link>
        </div>
        {runtime && (
          <div
            className={`runtime-notice ${runtime.durable ? "durable" : "temporary"}`}
          >
            <strong>
              {runtime.durable
                ? zh
                  ? "PostgreSQL 持久模式"
                  : "PostgreSQL persistence"
                : zh
                  ? "暫時工作階段"
                  : "Temporary session"}
            </strong>
            <span>
              {zh
                ? runtime.durable
                  ? "案件最長保留七天。"
                  : "目前沒有正式資料庫；案件可能在服務重新啟動後消失。"
                : runtime.notice}{" "}
              {zh
                ? `每個匿名工作階段最多 ${runtime.case_quota} 個有效案件。`
                : `Up to ${runtime.case_quota} active cases per anonymous session.`}
            </span>
          </div>
        )}
        <div className="case-toolbar">
          <label>
            <Search size={16} />
            <span className="sr-only">{zh ? "搜尋案件" : "Search cases"}</span>
            <input
              placeholder={
                zh ? "搜尋公司、案件或狀態" : "Search borrower, case, or status"
              }
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </label>
          <label className="archive-toggle">
            <input
              type="checkbox"
              checked={showArchived}
              onChange={(e) => setShowArchived(e.target.checked)}
            />
            {zh ? "顯示已封存" : "Show archived"}
          </label>
        </div>
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        {loading ? (
          <div className="center-state">
            <LoaderCircle className="spin" />
            <p>{zh ? "載入案件…" : "Loading cases…"}</p>
          </div>
        ) : shown.length === 0 ? (
          <div className="empty-state">
            <FolderOpen size={34} />
            <h2>
              {query
                ? zh
                  ? "沒有符合的案件"
                  : "No matching cases"
                : zh
                  ? "尚無案件"
                  : "No cases yet"}
            </h2>
            <p>
              {zh
                ? "從合成範本建立案件，所有重要輸入都可編輯。"
                : "Start from a synthetic template, then edit every material input."}
            </p>
            <Link className="button primary" href={`${root}/app/cases/new`}>
              {zh ? "建立第一個案件" : "Create your first case"}
            </Link>
          </div>
        ) : (
          <div className="case-list">
            {shown.map((item) => (
              <article key={item.id}>
                <div className="case-list-main">
                  <span className={`case-status ${item.status}`}>
                    {item.status}
                  </span>
                  <h2>{item.title}</h2>
                  <p>
                    {item.decision ??
                      (zh ? "尚未執行分析" : "Not analyzed yet")}
                    {item.grade
                      ? ` · ${zh ? "評等" : "Grade"} ${item.grade}`
                      : ""}
                  </p>
                  <small>
                    {zh ? "版本" : "Version"} {item.version} ·{" "}
                    {new Date(item.updated_at).toLocaleString(
                      zh ? "zh-TW" : "en-US",
                    )}
                  </small>
                </div>
                <div className="case-list-actions">
                  <Link
                    className="button secondary"
                    href={`${root}/app/cases/${item.id}/overview`}
                  >
                    <FolderOpen size={15} />
                    {zh ? "開啟" : "Open"}
                  </Link>
                  <button
                    title={zh ? "複製" : "Duplicate"}
                    onClick={() => act(item.id, "duplicate")}
                    disabled={busy === item.id}
                  >
                    <Copy size={16} />
                  </button>
                  <button
                    title={zh ? "封存或還原" : "Archive or restore"}
                    onClick={() => act(item.id, "archive")}
                    disabled={busy === item.id}
                  >
                    <Archive size={16} />
                  </button>
                  <button
                    className="danger"
                    title={zh ? "刪除" : "Delete"}
                    onClick={() => act(item.id, "delete")}
                    disabled={busy === item.id}
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </main>
    </>
  );
}
