export type SupportedLanguage = 'en' | 'hi' | 'bn' | 'ta' | 'te' | 'mixed';

export interface Citation {
  citation_number: number;
  document_title: string;
  section_no?: string | null;
  rule_no?: string | null;
  chapter?: string | null;
  page_number?: number | null;
  authority: string;
  source_url: string;
  status: string;
  is_current: boolean;
}

export interface EvidenceTrace {
  chunk_id: number;
  document_title?: string | null;
  section_no?: string | null;
  rule_no?: string | null;
  chapter?: string | null;
  domain?: string | null;
  authority?: string | null;
  authority_tier?: string | null;
  source_url?: string | null;
  page_number?: number | null;
  status?: string | null;
  reranker_score: number;
  content_preview: string;
}

export interface ChatMessage {
  id?: number | string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  language?: string;
  domain?: string;
  intent?: string;
  citations?: Citation[];
  evidence?: EvidenceTrace[];
  confidence?: number;
  evidence_level?: 'high' | 'moderate' | 'low' | 'none';
  warnings?: string[];
  retrieval_trace_id?: string;
  has_sufficient_evidence?: boolean;
  retrieval_latency_ms?: number;
  total_latency_ms?: number;
  created_at?: string;
}

export interface SourceItem {
  id: number;
  name: string;
  authority: string;
  authority_tier: string;
  domain: string;
  document_type?: string | null;
  url: string;
  description?: string | null;
  is_active: boolean;
  last_checked?: string | null;
  created_at: string;
}

export interface LawItem {
  id: number;
  title: string;
  domain: string;
  document_type: string;
  authority: string;
  status: string;
  source_url: string;
  page_count?: number | null;
  created_at: string;
}

export interface AdminStats {
  total_documents: number;
  total_chunks: number;
  total_sources: number;
  total_sessions: number;
  total_queries: number;
  domains_coverage: Record<string, number>;
  recent_jobs: IngestionJob[];
  avg_retrieval_latency_ms: number;
  avg_total_latency_ms: number;
  low_evidence_rate: number;
  helpful_feedback_rate: number;
}

export interface IngestionJob {
  id: number;
  source_url: string;
  status: string;
  chunks_created: number;
  duplicates_skipped: number;
  embeddings_generated: number;
  error_message?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  created_at: string;
}
