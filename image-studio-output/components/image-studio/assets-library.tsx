"use client";

import { useState, useEffect } from "react";
import { Loader2, X, ImageIcon } from "lucide-react";
import { toast } from "sonner";
import {
  Sheet,
  SheetContent,
  SheetClose,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

interface PoolImage {
  id: string;
  url: string;
  thumbnail_url?: string;
  tags: string[];
  filename: string;
}

interface AssetsLibraryProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  sessionId: string;
  targetSection: number | null;
  apiUrl: string;
  onImageSelected?: (sectionIndex: number) => void;
}

const TAG_COLOURS: Record<string, string> = {
  selling: "bg-orange-500/15 text-orange-400 border-orange-500/20",
  faq: "bg-purple-500/15 text-purple-400 border-purple-500/20",
  "bottom-line": "bg-blue-500/15 text-blue-400 border-blue-500/20",
  regular: "bg-muted text-muted-foreground",
};

function TagBadge({ tag }: { tag: string }) {
  const cls = TAG_COLOURS[tag] ?? TAG_COLOURS["regular"];
  return (
    <Badge className={cn("text-[10px] h-4 px-1.5 border", cls)}>
      {tag}
    </Badge>
  );
}

export function AssetsLibrary({
  open,
  onOpenChange,
  sessionId,
  targetSection,
  apiUrl,
  onImageSelected,
}: AssetsLibraryProps) {
  const [images, setImages] = useState<PoolImage[]>([]);
  const [loading, setLoading] = useState(false);
  const [applying, setApplying] = useState<string | null>(null);
  const [activeTag, setActiveTag] = useState<string>("all");

  useEffect(() => {
    if (open) {
      fetchPool();
    }
  }, [open]);

  async function fetchPool() {
    setLoading(true);
    try {
      const res = await fetch(`${apiUrl}/pool`);
      if (!res.ok) throw new Error(`${res.status}`);
      const data: PoolImage[] = await res.json();
      setImages(data);
    } catch {
      toast.error("Could not load asset pool.");
    } finally {
      setLoading(false);
    }
  }

  async function handleUseImage(image: PoolImage) {
    if (targetSection === null) {
      toast.error("No target section selected.");
      return;
    }
    setApplying(image.id);
    try {
      const res = await fetch(
        `${apiUrl}/sessions/${sessionId}/sections/${targetSection}/regen`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ source: "pool", pool_image_id: image.id }),
        }
      );
      if (!res.ok) throw new Error(`${res.status}`);
      toast.success("Regenerating with pool image…");
      onOpenChange(false);
      onImageSelected?.(targetSection);
    } catch {
      toast.error("Could not apply pool image.");
    } finally {
      setApplying(null);
    }
  }

  // Collect all unique tags
  const allTags = Array.from(new Set(images.flatMap((img) => img.tags)));

  const filtered =
    activeTag === "all"
      ? images
      : images.filter((img) => img.tags.includes(activeTag));

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" showCloseButton={false} className="w-full sm:max-w-md flex flex-col gap-0 p-0">
        {/* Header */}
        <SheetHeader className="px-5 pt-5 pb-4 border-b border-border flex-shrink-0">
          <div className="flex items-start justify-between">
            <div>
              <SheetTitle className="text-base font-semibold">
                Asset Pool
              </SheetTitle>
              <SheetDescription className="text-xs mt-0.5">
                {targetSection !== null
                  ? `Applying to Section ${targetSection}`
                  : "Click any image to use it as a background"}
              </SheetDescription>
            </div>
            <SheetClose className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors -mr-1">
              <X size={15} />
            </SheetClose>
          </div>

          {/* Tag filter */}
          {allTags.length > 0 && (
            <div className="flex items-center gap-1.5 flex-wrap mt-3">
              <button
                type="button"
                onClick={() => setActiveTag("all")}
                className={cn(
                  "px-2.5 py-0.5 rounded-full text-xs font-medium transition-all",
                  activeTag === "all"
                    ? "bg-[var(--teal)] text-white"
                    : "text-muted-foreground hover:text-foreground bg-muted/50 hover:bg-muted"
                )}
              >
                All ({images.length})
              </button>
              {allTags.map((tag) => (
                <button
                  key={tag}
                  type="button"
                  onClick={() => setActiveTag(tag)}
                  className={cn(
                    "px-2.5 py-0.5 rounded-full text-xs font-medium transition-all",
                    activeTag === tag
                      ? "bg-[var(--teal)] text-white"
                      : "text-muted-foreground hover:text-foreground bg-muted/50 hover:bg-muted"
                  )}
                >
                  {tag}
                </button>
              ))}
            </div>
          )}
        </SheetHeader>

        {/* Grid */}
        <div className="flex-1 overflow-y-auto px-4 py-4">
          {loading ? (
            <div className="grid grid-cols-2 gap-3">
              {Array.from({ length: 8 }).map((_, i) => (
                <Skeleton key={i} className="aspect-video rounded-lg" />
              ))}
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
              <div className="p-3 rounded-xl bg-muted/40">
                <ImageIcon size={28} className="text-muted-foreground/40" />
              </div>
              <p className="text-sm text-muted-foreground">No pool images found.</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-3">
              {filtered.map((image) => (
                <button
                  key={image.id}
                  type="button"
                  onClick={() => handleUseImage(image)}
                  disabled={applying !== null}
                  className="group relative rounded-lg overflow-hidden aspect-video bg-muted/30 focus:outline-none focus:ring-2 focus:ring-[var(--teal)] transition-all hover:ring-2 hover:ring-[var(--teal)]/60"
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={image.thumbnail_url ?? `${apiUrl}${image.url}`}
                    alt={image.filename}
                    className="w-full h-full object-cover transition-transform duration-200 group-hover:scale-105"
                  />
                  {/* Overlay */}
                  <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center">
                    {applying === image.id ? (
                      <Loader2
                        size={20}
                        className="text-white animate-spin"
                      />
                    ) : (
                      <span className="text-white text-xs font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                        Use this
                      </span>
                    )}
                  </div>
                  {/* Tags */}
                  {image.tags.length > 0 && (
                    <div className="absolute bottom-1.5 left-1.5 flex items-center gap-1 flex-wrap">
                      {image.tags.slice(0, 2).map((tag) => (
                        <TagBadge key={tag} tag={tag} />
                      ))}
                    </div>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
