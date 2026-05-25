"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  ImageIcon,
  Plus,
  Clock,
  CheckCircle,
  Loader2,
  FileText,
  Layers,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  CardAction,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogClose,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import type { ImageSession } from "@/types/image-studio";

const API_URL = process.env.NEXT_PUBLIC_IMAGE_STUDIO_API_URL ?? "http://localhost:8000";

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

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("en-CA", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function ImageStudioPage() {
  const router = useRouter();
  const [sessions, setSessions] = useState<ImageSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // New session form state
  const [articleTitle, setArticleTitle] = useState("");
  const [articleText, setArticleText] = useState("");
  const [isSelling, setIsSelling] = useState(false);

  useEffect(() => {
    fetchSessions();
  }, []);

  async function fetchSessions() {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/sessions`);
      if (!res.ok) throw new Error(`Server returned ${res.status}`);
      const data: ImageSession[] = await res.json();
      setSessions(data);
    } catch (err) {
      toast.error("Could not load sessions. Is the image service running?");
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateSession(e: React.FormEvent) {
    e.preventDefault();
    if (!articleTitle.trim()) {
      toast.error("Please enter an article title.");
      return;
    }
    if (!articleText.trim()) {
      toast.error("Please paste the article text.");
      return;
    }

    setSubmitting(true);
    try {
      const res = await fetch(`${API_URL}/sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          article_title: articleTitle.trim(),
          article_text: articleText.trim(),
          is_selling_article: isSelling,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? `Server returned ${res.status}`);
      }
      const session: ImageSession = await res.json();
      toast.success("Session created!");
      setDialogOpen(false);
      router.push(`/image-studio/${session.id}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      toast.error(`Failed to create session: ${msg}`);
    } finally {
      setSubmitting(false);
    }
  }

  function resetForm() {
    setArticleTitle("");
    setArticleText("");
    setIsSelling(false);
  }

  return (
    <div className="max-w-4xl mx-auto py-5">
      {/* Header */}
      <div className="flex items-center justify-between px-4 lg:px-6 mb-6">
        <div className="flex items-center gap-3">
          <ImageIcon size={20} className="text-muted-foreground" />
          <h1 className="text-lg font-semibold">Image Studio</h1>
        </div>
        <Button
          onClick={() => {
            resetForm();
            setDialogOpen(true);
          }}
          className="gap-1.5 bg-gradient-to-br from-[#5B8DEF] to-[#1A3FA0] text-white hover:opacity-90 border-0"
        >
          <Plus size={15} />
          New Session
        </Button>
      </div>

      {/* Sessions list */}
      <div className="px-4 lg:px-6 space-y-3">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-20 w-full rounded-xl" />
          ))
        ) : sessions.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
            <div className="p-4 rounded-2xl bg-muted/50">
              <ImageIcon size={36} className="text-muted-foreground/50" />
            </div>
            <div>
              <p className="font-medium text-foreground">No sessions yet</p>
              <p className="text-sm text-muted-foreground mt-1">
                Create your first session to start generating blog images.
              </p>
            </div>
            <Button
              variant="outline"
              onClick={() => {
                resetForm();
                setDialogOpen(true);
              }}
              className="gap-1.5 mt-2"
            >
              <Plus size={14} />
              New Session
            </Button>
          </div>
        ) : (
          sessions.map((session) => (
            <button
              key={session.id}
              onClick={() => router.push(`/image-studio/${session.id}`)}
              className="w-full text-left"
            >
              <Card className="hover:ring-[var(--teal)]/30 hover:ring-2 transition-all duration-150 cursor-pointer py-3">
                <CardHeader className="border-b-0 pb-0">
                  <CardTitle className="text-sm font-medium leading-snug line-clamp-1">
                    {session.article_title}
                  </CardTitle>
                  <CardDescription className="text-xs">
                    {formatDate(session.created_at)}
                  </CardDescription>
                  <CardAction>
                    <StatusBadge status={session.status} />
                  </CardAction>
                </CardHeader>
                <CardContent className="pt-2 pb-0">
                  <div className="flex items-center gap-3 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Layers size={11} />
                      {session.section_count} section
                      {session.section_count !== 1 ? "s" : ""}
                    </span>
                    {session.is_selling_article && (
                      <Badge
                        variant="outline"
                        className="text-[10px] h-4 px-1.5 border-orange-500/30 text-orange-400"
                      >
                        Selling
                      </Badge>
                    )}
                  </div>
                </CardContent>
              </Card>
            </button>
          ))
        )}
      </div>

      {/* New Session Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent showCloseButton={false} className="sm:max-w-lg p-0">
          <div className="flex items-center justify-between px-5 pt-5 pb-4 border-b border-border">
            <div>
              <h2 className="text-base font-semibold">New Image Session</h2>
              <p className="text-xs text-muted-foreground mt-0.5">
                Paste your article and the backend will plan all image sections.
              </p>
            </div>
            <DialogClose className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors">
              ×
            </DialogClose>
          </div>

          <form onSubmit={handleCreateSession} className="px-5 py-4 flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Article Title
              </label>
              <Input
                value={articleTitle}
                onChange={(e) => setArticleTitle(e.target.value)}
                placeholder="e.g. Should You Sell Before Things Get Worse?"
                disabled={submitting}
                required
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Article Text
              </label>
              <Textarea
                value={articleText}
                onChange={(e) => setArticleText(e.target.value)}
                placeholder="Paste the full article content here…"
                className="min-h-[180px] font-mono text-xs resize-y"
                disabled={submitting}
                required
              />
            </div>

            <label className="flex items-center gap-2.5 cursor-pointer select-none">
              <div
                role="checkbox"
                aria-checked={isSelling}
                onClick={() => setIsSelling((v) => !v)}
                className={`w-4 h-4 rounded border flex items-center justify-center transition-colors ${
                  isSelling
                    ? "bg-[var(--teal)] border-[var(--teal)]"
                    : "border-border bg-transparent"
                }`}
              >
                {isSelling && (
                  <svg
                    viewBox="0 0 10 8"
                    fill="none"
                    className="w-2.5 h-2"
                    stroke="white"
                    strokeWidth="2"
                  >
                    <path d="M1 4l3 3 5-6" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                )}
              </div>
              <span className="text-sm text-foreground">
                This is a selling / CTA-focused article
              </span>
            </label>

            <div className="flex items-center justify-end gap-2 pt-1">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setDialogOpen(false)}
                disabled={submitting}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                size="sm"
                disabled={submitting}
                className="bg-gradient-to-br from-[#5B8DEF] to-[#1A3FA0] text-white border-0 hover:opacity-90 gap-1.5"
              >
                {submitting ? (
                  <>
                    <Loader2 size={13} className="animate-spin" />
                    Creating…
                  </>
                ) : (
                  <>
                    <Plus size={13} />
                    Create Session
                  </>
                )}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
