export interface UserOut {
  id: number;
  username: string;
  email: string;
  created_at: string;
}

export type ToleranceType = 'absolute' | 'percentage';

export interface SessionOut {
  id: number;
  ledger_filename: string;
  bank_filename: string;
  additional_bank_filenames: string | null;
  ledger_source: 'pdf' | 'manual';
  date_tolerance_days: number;
  amount_tolerance: number;
  tolerance_type: ToleranceType;
  description_threshold: number;
  status: 'pending' | 'processing' | 'done' | 'error';
  progress_pct: number;
  error_message: string | null;
  created_at: string;
}

export interface ProgressOut {
  status: 'pending' | 'processing' | 'done' | 'error';
  progress_pct: number;
  error_message: string | null;
}

export type MatchStatus = 'Matched' | 'Matched (tolerance)' | 'Partial' | 'Missing';

export interface MatchResultOut {
  id: number;
  date: string;
  ledger_description: string | null;
  ledger_amount: string | null;
  bank_narration: string | null;
  bank_amount: string | null;
  bank_label: string | null;
  match_status: MatchStatus;
  reason: string | null;
  tolerance_applied: boolean;
  is_duplicate: boolean;
  similarity_score: number | null;
  amount_diff: number | null;
  date_diff_days: number | null;
}

export interface HistoryMatchOut extends MatchResultOut {
  session_id: number;
  session_created_at: string;
  ledger_filename: string;
  bank_filename: string;
}

export interface HistorySearchFilters {
  date_from?: string;
  date_to?: string;
  amount_diff_min?: number;
  date_diff_min?: number;
  status_filter?: string;
  duplicates_only?: boolean;
  tolerance_only?: boolean;
}

export interface LedgerEntryOut {
  id: number;
  txn_date: string;
  description: string;
  amount: string;
  ref_no: string | null;
  created_at: string;
  updated_at: string;
}

export interface LedgerEntryIn {
  txn_date: string;
  description: string;
  amount: string;
  ref_no: string | null;
}

export interface SummaryOut {
  matched: number;
  partial: number;
  unmatched: number;
  total: number;
}

export interface ResultsPage {
  summary: SummaryOut;
  items: MatchResultOut[];
  page: number;
  page_size: number;
  total_items: number;
}
