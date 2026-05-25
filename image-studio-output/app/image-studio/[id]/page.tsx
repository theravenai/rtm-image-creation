"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useParams } from "next/navigation";
import {
  Download,
  Loader2,
  Play,
  CheckCircle,
  Clock,
  FileText,
  Layers,
  ImageIcon,
  Images,
  ThumbsUp,
  ChevronDown,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { SectionCard } from "@/components/image-studio/section-card";
import { AssetsLibrary } from "@/components/image-studio/assets-library";
import { cn } from "@/lib/utils";
import type { ImageSection, ImageSession } from "@/types/image-studio";

const API_URL =
  process.env.NEXT_PUBLIC_IMAGE_STUDIO_API_URL ?? "http://localhost:8000";

// ── Status badge ────────────────────────────────────────────────────────────
function StatusBadge({ status }: { status: ImageSession["status"] }) {
  if (status === "draft") {
    return (
      <Badge variant="secondary" className="gap-1 text-muted-foreground">
        <Clock size={10} />
        Draft
      </Badge>
    );
  }
  if (status === "generating") {
    return (
      <Badge className="gap-1 bg-blue-500/15 text-blue-400 border-blue-500/20">
        <Loader2 size={10} className="animate-spin" />
        Generating
      </Badge>
    );
  }
  if (status === "reviewing") {
    return (
      <Badge className="gap-1 bg-yellow-500/15 text-yellow-400 border-yellow-500/20">
        <FileText size={10} />
        Reviewing
      </Badge>
    );
  }
  return (
    <Badge className="gap-1 bg-green-500/15 text-green-400 border-green-500/20">
      <CheckCircle size={10} />
      Complete
    </Badge>
  );
}

// ── Mini sidebar section item ───────────────────────────────────────────────
function SidebarSectionItem({
  section,
  onClick,
}: {
  section: ImageSection;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full flex items-start gap-2 px-3 py-1.5 rounded-lg text-left hover:bg-muted/50 transition-colors group"
    >
      <span className="flex-shrink-0 w-5 h-5 rounded-full bg-muted flex items-center justify-center text-[10px] font-medium text-muted-foreground group-hover:text-foreground mt-0.5">
        {section.section_number}
      </span>
      <div className="flex-1 min-w-0">
        <p className="text-xs text-muted-foreground group-hover:text-foreground transition-colors line-clamp-2 leading-snug">
          {section.h2_text}
        </p>
        <div className="flex items-center gap-1 mt-0.5">
          {section.rating === 1 && (
            <span className="text-[9px] text-green-400">✓ approved</span>
          )}
          {section.rating === -1 && (
            <span className="text-[9px] text-red-400">✗ rejected</span>
          )}
          {section.status === "generating" && (
            <Loader2 size={9} className="text-blue-400 animate-spin" />
          )}
        </div>
      </div>
    </button>
  );
}

export default function ImageSessionPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;

  const [session, setSession] = useState<ImageSession | null>(null);
  const [sections, setSections] = useState<ImageSection[]>([]);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [assetsOpen, setAssetsOpen] = useState(false);
  const [assetsTargetSection, setAssetsTargetSection] = useState<number | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  // ── Fetch session ──────────────────────────────────────────────────────────
  const fetchSession = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/sessions/${id}`);
      if (!res.ok) throw new Error(`${res.status}`);
      const data: ImageSession = await res.json();
      setSession(data);
      setSections(data.sections ?? []);
      return data;
    } catch (err) {
      toast.error("Could not load session.");
      return null;
    } finally {
      setLoading(false);
    }
  }, [id]);

  // ── SSE connection ─────────────────────────────────────────────────────────
  const connectSSE = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    const es = new EventSource(`${API_URL}/sessions/${id}/stream`);
    eventSourceRef.current = es;

    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data as string);

        if (data.type === "section_start") {
          setSections((prev) =>
            prev.map((s) =>
              s.section_number === data.section_number
                ? { ...s, status: "generating" }
                : s
            )
          );
        }

        if (data.type === "section_done") {
          setSections((prev) =>
            prev.map((s) =>
              s.section_number === data.section_number
                ? {
                    ...s,
                    status: "done",
                    composited_url: data.composited_url ?? s.composited_url,
                    background_url: data.background_url ?? s.background_url,
                    prompt: data.prompt ?? s.prompt,
                    source: data.source ?? s.source,
                  }
                : s
            )
          );
        }

        if (data.type === "all_done") {
          es.close();
          eventSourceRef.current = null;
          setSession((prev) =>
            prev ? { ...prev, status: "reviewing" } : prev
          );
          toast.success("All images generated!");
        }

        if (data.type === "error") {
          toast.error(`Generation error: ${data.message ?? "Unknown error"}`);
        }
      } catch {
        // Ignore malformed SSE
      }
    };

    es.onerror = () => {
      // Reconnect only if still generating
      setSession((current) => {
        if (current?.status === "generating") {
          setTimeout(connectSSE, 3000);
        }
        return current;
      });
    };
  }, [id]);

  // ── Mount ──────────────────────────────────────────────────────────────────
  useEffect(() => {
    fetchSession().then((data) => {
      if (data?.status === "generating") {
        connectSSE();
      }
    });
    return () => {
      eventSourceRef.current?.close();
    };
  }, [fetchSession, connectSSE]);

  // ── Start generation ───────────────────────────────────────────────────────
  async function handleStartGeneration() {
    setStarting(true);
    try {
      const res = await fetch(`${API_URL}/sessions/${id}/start`, {
        method: "POST",
      });
      if (!res.ok) throw new Error(`${res.status}`);
      const data: ImageSession = await res.json();
      setSession(data);
      setSections(data.sections ?? []);
      connectSSE();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      toast.error(`Could not start generation: ${msg}`);
    } finally {
      setStarting(false);
    }
  }

  // ── Section update (optimistic) ────────────────────────────────────────────
  function handleSectionUpdate(
    sectionNumber: number,
    updates: Partial<ImageSection>
  ) {
    setSections((prev) =>
      prev.map((s) =>
        s.section_number === sectionNumber ? { ...s, ...updates } : s
      )
    );
  }

  // ── Regenerate ─────────────────────────────────────────────────────────────
  async function handleRegenerate(sectionNumber: number, prompt?: string) {
    handleSectionUpdate(sectionNumber, { status: "generating" });
    try {
      const body: Record<string, unknown> = {};
      if (prompt) body.prompt = prompt;
      const res = await fetch(
        `${API_URL}/sessions/${id}/sections/${sectionNumber}/regen`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        }
      );
      if (!res.ok) throw new Error(`${res.status}`);
      const updated: ImageSection = await res.json();
      handleSectionUpdate(sectionNumber, updated);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      toast.error(`Regen failed: ${msg}`);
      handleSectionUpdate(sectionNumber, { status: "done" });
    }
  }

  // ── Recomposite ────────────────────────────────────────────────────────────
  async function handleRecomposite(sectionNumber: number, position: string) {
    try {
      const res = await fetch(
        `${API_URL}/sessions/${id}/sections/${sectionNumber}/recomposite`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ position }),
        }
      );
      if (!res.ok) throw new Error(`${res.status}`);
      const updated: ImageSection = await res.json();
      handleSectionUpdate(sectionNumber, {
        composited_url: updated.composited_url,
        force_position: updated.force_position,
      });
    } catch {
      toast.error("Recomposite failed.");
    }
  }

  // ── Download ───────────────────────────────────────────────────────────────
  function handleDownload() {
    window.location.href = `${API_URL}/sessions/${id}/download`;
  }

  // ── Approval count ─────────────────────────────────────────────────────────
  const approvedCount = sections.filter((s) => s.rating === 1).length;
  const totalCount = sections.length;

  // ── Open asset library for a section ──────────────────────────────────────
  function openAssetsFor(sectionNumber: number) {
    setAssetsTargetSection(sectionNumber);
    setAssetsOpen(true);
  }

  // ── Loading ────────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="flex h-[calc(100dvh-48px)]">
        {/* Sidebar skeleton */}
        <div className="hidden lg:flex flex-col w-[300px] flex-shrink-0 border-r border-border/50 p-4 gap-3">
          <Skeleton className="h-6 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
          <Skeleton className="h-8 w-full mt-2" />
          <div className="flex flex-col gap-1.5 mt-2">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-8 w-full" />
            ))}
          </div>
        </div>
        {/* Main skeleton */}
        <div className="flex-1 p-5 grid grid-cols-1 md:grid-cols-2 gap-4 content-start overflow-y-auto">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-64 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="flex items-center justify-center h-[60vh] flex-col gap-3">
        <ImageIcon size={40} className="text-muted-foreground/30" />
        <p className="text-muted-foreground text-sm">Session not found.</p>
      </div>
    );
  }

  return (
    <div className="flex h-[calc(100dvh-48px)] overflow-hidden">
      {/* ── Left Sidebar ─────────────────────────────────────────────────── */}
      <aside
        className={cn(
          "hidden lg:flex flex-col flex-shrink-0 border-r border-border/50 bg-card/30 transition-all duration-200 overflow-y-auto",
          sidebarCollapsed ? "w-12" : "w-[300px]"
        )}
      >
        {sidebarCollapsed ? (
          <button
            type="button"
            onClick={() => setSidebarCollapsed(false)}
            className="flex items-center justify-center p-3 mt-2 mx-auto text-muted-foreground hover:text-foreground"
          >
            <ChevronDown size={16} className="-rotate-90" />
          </button>
        ) : (
          <div className="px-4 py-5 flex flex-col gap-4 min-h-0">
            {/* Title + collapse */}
            <div className="flex items-start justify-between gap-2">
              <h2 className="text-sm font-semibold leading-snug line-clamp-3 flex-1">
                {session.article_title}
              </h2>
              <button
                type="button"
                onClick={() => setSidebarCollapsed(true)}
                className="p-1 rounded text-muted-foreground/40 hover:text-muted-foreground flex-shrink-0 mt-0.5"
              >
                <ChevronDown size={13} className="rotate-90" />
              </button>
            </div>

            {/* Status + meta */}
            <div className="flex items-center gap-2 flex-wrap">
              <StatusBadge status={session.status} />
              {session.is_selling_article && (
                <Badge
                  variant="outline"
                  className="text-[10px] h-4 px-1.5 border-orange-500/30 text-orange-400"
                >
                  Selling
                </Badge>
              )}
            </div>

            {/* Approval counter */}
            <div className="flex items-center gap-2 p-3 rounded-lg bg-muted/30">
              <ThumbsUp size={14} className="text-green-400 flex-shrink-0" />
              <div>
                <p className="text-xs font-medium">
                  {approvedCount} of {totalCount} approved
                </p>
                <div className="mt-1 h-1.5 rounded-full bg-muted overflow-hidden">
                  <div
                    className="h-full rounded-full bg-green-500 transition-all duration-300"
                    style={{
                      width:
                        totalCount > 0
                          ? `${(approvedCount / totalCount) * 100}%`
                          : "0%",
                    }}
                  />
                </div>
              </div>
            </div>

            {/* Section count */}
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Layers size={12} />
              {totalCount} section{totalCount !== 1 ? "s" : ""}
            </div>

            {/* Download button */}
            {(session.status === "reviewing" || session.status === "complete") && (
              <Button
                onClick={handleDownload}
                className="gap-1.5 bg-gradient-to-br from-[#5B8DEF] to-[#1A3FA0] text-white border-0 hover:opacity-90 w-full"
              >
                <Download size={14} />
                Download All
              </Button>
            )}

            {/* Asset pool button */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setAssetsTargetSection(null);
                setAssetsOpen(true);
              }}
              className="gap-1.5 w-full"
            >
              <Images size={13} />
              Asset Pool
            </Button>

            {/* Sections nav */}
            {sections.length > 0 && (
              <div className="flex flex-col gap-0.5 mt-1">
                <p className="px-3 text-[10px] font-semibold tracking-widest uppercase text-muted-foreground/50 mb-1">
                  Sections
                </p>
                {sections.map((s) => (
                  <SidebarSectionItem
                    key={s.section_number}
                    section={s}
                    onClick={() => {
                      const el = document.getElementById(
                        `section-${s.section_number}`
                      );
                      el?.scrollIntoView({ behavior: "smooth", block: "start" });
                    }}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </aside>

      {/* ── Main content ──────────────────────────────────────────────────── */}
      <main className="flex-1 min-w-0 overflow-y-auto">
        <div className="max-w-5xl mx-auto px-4 lg:px-6 py-5">
          {/* Mobile header */}
          <div className="lg:hidden mb-4 flex items-start justify-between gap-3">
            <div>
              <h1 className="text-base font-semibold leading-snug">
                {session.article_title}
              </h1>
              <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                <StatusBadge status={session.status} />
                <span className="text-xs text-muted-foreground">
                  {approvedCount}/{totalCount} approved
                </span>
              </div>
            </div>
            {(session.status === "reviewing" ||
              session.status === "complete") && (
              <Button
                size="sm"
                onClick={handleDownload}
                className="gap-1.5 bg-gradient-to-br from-[#5B8DEF] to-[#1A3FA0] text-white border-0 hover:opacity-90 flex-shrink-0"
              >
                <Download size={13} />
                Download
              </Button>
            )}
          </div>

          {/* Draft CTA */}
          {session.status === "draft" && (
            <div className="mb-6 flex flex-col items-center justify-center py-12 gap-4 rounded-xl bg-card ring-1 ring-foreground/10 text-center">
              <div className="p-4 rounded-2xl bg-muted/50">
                <ImageIcon size={36} className="text-muted-foreground/40" />
              </div>
              <div>
                <p className="font-medium">Ready to generate images</p>
                <p className="text-sm text-muted-foreground mt-1">
                  The session has been planned.{" "}
                  {session.section_count > 0 && (
                    <>
                      {session.section_count} section
                      {session.section_count !== 1 ? "s" : ""} queued.{" "}
                    </>
                  )}
                  Start generation when ready.
                </p>
              </div>
              <Button
                onClick={handleStartGeneration}
                disabled={starting}
                className="gap-1.5 bg-gradient-to-br from-[#5B8DEF] to-[#1A3FA0] text-white border-0 hover:opacity-90"
              >
                {starting ? (
                  <>
                    <Loader2 size={15} className="animate-spin" />
                    Starting…
                  </>
                ) : (
                  <>
                    <Play size={15} />
                    Start Generation
                  </>
                )}
              </Button>
            </div>
          )}

          {/* Sections grid */}
          {sections.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {sections.map((section) => (
                <SectionCard
                  key={section.section_number}
                  section={section}
                  sessionId={id}
                  onUpdate={handleSectionUpdate}
                  onRegenerate={handleRegenerate}
                  onRecomposite={handleRecomposite}
                  apiUrl={API_URL}
                />
              ))}
            </div>
          ) : session.status !== "draft" ? (
            <div className="flex items-center justify-center py-20 flex-col gap-3 text-center">
              <Loader2 size={24} className="animate-spin text-muted-foreground/50" />
              <p className="text-sm text-muted-foreground">
                Waiting for sections…
              </p>
            </div>
          ) : null}
        </div>
      </main>

      {/* Asset library sheet */}
      <AssetsLibrary
        open={assetsOpen}
        onOpenChange={setAssetsOpen}
        sessionId={id}
        targetSection={assetsTargetSection}
        apiUrl={API_URL}
        onImageSelected={(sectionNumber) => {
          handleSectionUpdate(sectionNumber, { status: "generating" });
        }}
      />
    </div>
  );
}
