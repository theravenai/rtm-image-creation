"use client";

import { useState, useRef } from "react";
import {
  ChevronDown,
  ChevronUp,
  ThumbsUp,
  ThumbsDown,
  RotateCcw,
  Edit3,
  Check,
  X,
  Loader2,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import type { ImageSection } from "@/types/image-studio";

export interface SectionCardProps {
  section: ImageSection;
  sessionId: string;
  onUpdate: (sectionIndex: number, updates: Partial<ImageSection>) => void;
  onRegenerate: (sectionIndex: number, prompt?: string) => void;
  onRecomposite: (sectionIndex: number, position: string) => void;
  apiUrl: string;
}

function SectionTypeBadge({ section }: { section: ImageSection }) {
  if (section.is_faq) {
    return (
      <Badge className="bg-purple-500/15 text-purple-400 border-purple-500/20 text-[10px]">
        FAQ
      </Badge>
    );
  }
  if (section.is_bottom_line) {
    return (
      <Badge className="bg-orange-500/15 text-orange-400 border-orange-500/20 text-[10px]">
        BOTTOM-LINE
      </Badge>
    );
  }
  return (
    <Badge variant="secondary" className="text-[10px]">
      REGULAR
    </Badge>
  );
}

function SourceBadge({ source }: { source: ImageSection["source"] }) {
  if (source === "gemini") {
    return (
      <Badge className="bg-blue-500/15 text-blue-400 border-blue-500/20 text-[10px]">
        AI
      </Badge>
    );
  }
  if (source === "pexels") {
    return (
      <Badge className="bg-teal-500/15 text-teal-400 border-teal-500/20 text-[10px]">
        PEXELS
      </Badge>
    );
  }
  return (
    <Badge className="bg-yellow-500/15 text-yellow-400 border-yellow-500/20 text-[10px]">
      POOL
    </Badge>
  );
}

export function SectionCard({
  section,
  sessionId,
  onUpdate,
  onRegenerate,
  onRecomposite,
  apiUrl,
}: SectionCardProps) {
  const [promptExpanded, setPromptExpanded] = useState(false);
  const [editingPrompt, setEditingPrompt] = useState(false);
  const [editedPrompt, setEditedPrompt] = useState(section.prompt ?? "");
  const [editingFilename, setEditingFilename] = useState(false);
  const [editedFilename, setEditedFilename] = useState(section.filename);
  const [rerunning, setRerunning] = useState(false);
  const [savingRating, setSavingRating] = useState(false);
  const [savingNotes, setSavingNotes] = useState(false);
  const notesTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const isGenerating = section.status === "generating" || section.status === "pending";
  const imageUrl = section.composited_url
    ? `${apiUrl}${section.composited_url}`
    : null;

  // ── Rating ────────────────────────────────────────────────────────────────
  async function handleRate(value: -1 | 1) {
    const newRating: -1 | 0 | 1 = section.rating === value ? 0 : value;
    onUpdate(section.section_number, { rating: newRating });
    setSavingRating(true);
    try {
      const res = await fetch(
        `${apiUrl}/sessions/${sessionId}/sections/${section.section_number}/rate`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ rating: newRating }),
        }
      );
      if (!res.ok) throw new Error(`${res.status}`);
    } catch (err) {
      toast.error("Could not save rating.");
      onUpdate(section.section_number, { rating: section.rating });
    } finally {
      setSavingRating(false);
    }
  }

  // ── Notes ─────────────────────────────────────────────────────────────────
  function handleNotesChange(value: string) {
    onUpdate(section.section_number, { notes: value });
    if (notesTimer.current) clearTimeout(notesTimer.current);
    notesTimer.current = setTimeout(async () => {
      setSavingNotes(true);
      try {
        const res = await fetch(
          `${apiUrl}/sessions/${sessionId}/sections/${section.section_number}/notes`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ notes: value }),
          }
        );
        if (!res.ok) throw new Error(`${res.status}`);
      } catch {
        toast.error("Could not save notes.");
      } finally {
        setSavingNotes(false);
      }
    }, 800);
  }

  // ── Position ──────────────────────────────────────────────────────────────
  function handlePositionToggle(pos: "lower-left" | "center") {
    if (section.force_position === pos) return;
    onUpdate(section.section_number, { force_position: pos });
    onRecomposite(section.section_number, pos);
  }

  // ── Filename edit ─────────────────────────────────────────────────────────
  async function saveFilename() {
    setEditingFilename(false);
    if (editedFilename === section.filename) return;
    onUpdate(section.section_number, { filename: editedFilename });
    try {
      const res = await fetch(
        `${apiUrl}/sessions/${sessionId}/sections/${section.section_number}/filename`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ filename: editedFilename }),
        }
      );
      if (!res.ok) throw new Error(`${res.status}`);
    } catch {
      toast.error("Could not save filename.");
      onUpdate(section.section_number, { filename: section.filename });
      setEditedFilename(section.filename);
    }
  }

  // ── Rerun ─────────────────────────────────────────────────────────────────
  async function handleRerun() {
    setRerunning(true);
    try {
      await onRegenerate(
        section.section_number,
        editingPrompt ? editedPrompt : undefined
      );
      setEditingPrompt(false);
    } finally {
      setRerunning(false);
    }
  }

  // ── Generating skeleton ───────────────────────────────────────────────────
  if (isGenerating) {
    return (
      <div
        id={`section-${section.section_number}`}
        className="rounded-xl bg-card ring-1 ring-foreground/10 overflow-hidden"
      >
        <div className="p-4 flex items-start gap-3">
          <div className="flex-shrink-0 w-7 h-7 rounded-full bg-muted/70 flex items-center justify-center text-xs font-medium text-muted-foreground animate-pulse">
            {section.section_number}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <Skeleton className="h-4 w-48" />
              <Skeleton className="h-4 w-16 rounded-full" />
            </div>
            <p className="text-xs text-muted-foreground flex items-center gap-1.5">
              <Loader2 size={11} className="animate-spin" />
              Generating…
            </p>
            {section.prompt && (
              <p className="font-mono text-[10px] text-muted-foreground/60 mt-1.5 line-clamp-2">
                {section.prompt}
              </p>
            )}
          </div>
        </div>
        <Skeleton className="h-40 mx-4 mb-4 rounded-lg" />
      </div>
    );
  }

  return (
    <div
      id={`section-${section.section_number}`}
      className={cn(
        "rounded-xl bg-card ring-1 ring-foreground/10 overflow-hidden transition-all",
        section.rating === 1 && "ring-green-500/30",
        section.rating === -1 && "ring-red-500/30"
      )}
    >
      {/* Card header */}
      <div className="px-4 pt-4 pb-3 flex items-start gap-3">
        <div className="flex-shrink-0 w-7 h-7 rounded-full bg-muted flex items-center justify-center text-xs font-semibold text-muted-foreground">
          {section.section_number}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start gap-2 flex-wrap">
            <h3 className="text-sm font-medium leading-snug flex-1 min-w-0">
              {section.h2_text}
            </h3>
            <div className="flex items-center gap-1.5 flex-shrink-0">
              <SectionTypeBadge section={section} />
              <SourceBadge source={section.source} />
            </div>
          </div>
        </div>
      </div>

      {/* Image area */}
      <div className="mx-4 mb-3 relative rounded-lg overflow-hidden bg-muted/30 aspect-video">
        {imageUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={imageUrl}
            alt={section.h2_text}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-xs text-muted-foreground/50">
            No image
          </div>
        )}
      </div>

      {/* Prompt section */}
      <div className="mx-4 mb-3 rounded-lg bg-muted/30 overflow-hidden">
        <button
          type="button"
          onClick={() => setPromptExpanded((v) => !v)}
          className="w-full flex items-center justify-between px-3 py-2 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          <span className="font-medium">Prompt</span>
          <div className="flex items-center gap-1.5">
            {!promptExpanded && section.prompt && (
              <span className="font-mono text-[10px] opacity-60 max-w-[200px] truncate">
                {section.prompt}
              </span>
            )}
            {promptExpanded ? (
              <ChevronUp size={13} />
            ) : (
              <ChevronDown size={13} />
            )}
          </div>
        </button>

        {promptExpanded && (
          <div className="px-3 pb-3 flex flex-col gap-2">
            {editingPrompt ? (
              <Textarea
                value={editedPrompt}
                onChange={(e) => setEditedPrompt(e.target.value)}
                className="font-mono text-xs min-h-[100px] resize-y bg-background/50"
              />
            ) : (
              <pre className="font-mono text-xs text-muted-foreground whitespace-pre-wrap break-words leading-relaxed">
                {section.prompt ?? "(no prompt)"}
              </pre>
            )}
            <div className="flex items-center gap-2">
              {editingPrompt ? (
                <>
                  <Button
                    size="xs"
                    variant="ghost"
                    onClick={() => {
                      setEditingPrompt(false);
                      setEditedPrompt(section.prompt ?? "");
                    }}
                  >
                    <X size={11} />
                    Cancel
                  </Button>
                  <Button
                    size="xs"
                    onClick={handleRerun}
                    disabled={rerunning}
                    className="gap-1 bg-gradient-to-br from-[#5B8DEF] to-[#1A3FA0] text-white border-0"
                  >
                    {rerunning ? (
                      <Loader2 size={11} className="animate-spin" />
                    ) : (
                      <RotateCcw size={11} />
                    )}
                    Run with Edit
                  </Button>
                </>
              ) : (
                <Button
                  size="xs"
                  variant="outline"
                  onClick={() => {
                    setEditedPrompt(section.prompt ?? "");
                    setEditingPrompt(true);
                  }}
                >
                  <Edit3 size={11} />
                  Edit &amp; Rerun
                </Button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Controls row */}
      <div className="px-4 pb-3 flex items-center gap-2 flex-wrap">
        {/* Rating */}
        <div className="flex items-center gap-1">
          <button
            type="button"
            disabled={savingRating}
            onClick={() => handleRate(1)}
            className={cn(
              "flex items-center gap-1 px-2 py-1 rounded-lg text-xs transition-all",
              section.rating === 1
                ? "bg-green-500/20 text-green-400 ring-1 ring-green-500/30"
                : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
            )}
          >
            <ThumbsUp size={13} />
          </button>
          <button
            type="button"
            disabled={savingRating}
            onClick={() => handleRate(-1)}
            className={cn(
              "flex items-center gap-1 px-2 py-1 rounded-lg text-xs transition-all",
              section.rating === -1
                ? "bg-red-500/20 text-red-400 ring-1 ring-red-500/30"
                : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
            )}
          >
            <ThumbsDown size={13} />
          </button>
        </div>

        {/* Position toggle — only for regular sections */}
        {!section.is_bottom_line && !section.is_faq && (
          <div className="flex items-center rounded-lg overflow-hidden ring-1 ring-border text-xs">
            {(["lower-left", "center"] as const).map((pos) => {
              const label = pos === "lower-left" ? "LEFT" : "CENTER";
              const active = (section.force_position ?? "lower-left") === pos;
              return (
                <button
                  key={pos}
                  type="button"
                  onClick={() => handlePositionToggle(pos)}
                  className={cn(
                    "px-2.5 py-1 transition-all font-medium",
                    active
                      ? "bg-[var(--teal)] text-white"
                      : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                  )}
                >
                  {label}
                </button>
              );
            })}
          </div>
        )}

        {/* Rerun button */}
        <Button
          size="xs"
          variant="outline"
          disabled={rerunning}
          onClick={handleRerun}
          className="ml-auto"
        >
          {rerunning ? (
            <Loader2 size={11} className="animate-spin" />
          ) : (
            <RotateCcw size={11} />
          )}
          Rerun
        </Button>
      </div>

      {/* Filename row */}
      <div className="px-4 pb-3 flex items-center gap-2">
        <span className="text-[10px] text-muted-foreground/60 font-mono flex-shrink-0">
          filename
        </span>
        {editingFilename ? (
          <div className="flex items-center gap-1.5 flex-1 min-w-0">
            <Input
              value={editedFilename}
              onChange={(e) => setEditedFilename(e.target.value)}
              className="h-6 text-xs font-mono py-0 px-2"
              onKeyDown={(e) => {
                if (e.key === "Enter") saveFilename();
                if (e.key === "Escape") {
                  setEditingFilename(false);
                  setEditedFilename(section.filename);
                }
              }}
              autoFocus
            />
            <button
              type="button"
              onClick={saveFilename}
              className="text-muted-foreground hover:text-green-400 transition-colors"
            >
              <Check size={13} />
            </button>
            <button
              type="button"
              onClick={() => {
                setEditingFilename(false);
                setEditedFilename(section.filename);
              }}
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              <X size={13} />
            </button>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => setEditingFilename(true)}
            className="flex items-center gap-1.5 group text-left"
          >
            <span className="font-mono text-[11px] text-muted-foreground group-hover:text-foreground transition-colors">
              {section.filename}
            </span>
            <Edit3
              size={11}
              className="text-muted-foreground/30 group-hover:text-muted-foreground transition-colors"
            />
          </button>
        )}
      </div>

      {/* Notes — shown when thumbs down or when there are existing notes */}
      {(section.rating === -1 || section.notes) && (
        <div className="px-4 pb-4">
          <Textarea
            value={section.notes}
            onChange={(e) => handleNotesChange(e.target.value)}
            placeholder={
              section.rating === -1
                ? "Add rejection notes…"
                : "Notes on this section…"
            }
            className="text-xs min-h-[60px] resize-none bg-muted/20"
          />
          {savingNotes && (
            <p className="text-[10px] text-muted-foreground/50 mt-1">
              Saving…
            </p>
          )}
        </div>
      )}
    </div>
  );
}
