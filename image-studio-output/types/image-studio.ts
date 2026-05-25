export interface ImageSection {
  section_number: number;
  h2_text: string;
  filename: string;
  is_bottom_line: boolean;
  is_faq: boolean;
  prompt: string | null;
  search_term: string | null;
  source: "gemini" | "pexels" | "pool";
  background_url: string | null;
  composited_url: string | null;
  force_position: "lower-left" | "center" | "upper-left" | null;
  rating: -1 | 0 | 1;
  notes: string;
  status: "pending" | "generating" | "done" | "approved" | "rejected";
}

export interface ImageSession {
  id: string;
  article_title: string;
  status: "draft" | "generating" | "reviewing" | "complete";
  is_selling_article: boolean;
  manifest: Record<string, unknown>;
  sections: ImageSection[];
  section_count: number;
  created_at: string;
}
