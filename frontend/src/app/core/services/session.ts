import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { HistoryMatchOut, HistorySearchFilters, ProgressOut, ResultsPage, SessionOut, ToleranceType } from '../models';

const API_BASE = '/api/sessions';

export interface UploadOptions {
  ledgerFile: File | null;
  useManualLedger: boolean;
  bankFiles: File[]; // 1 to 3 bank statement files, pooled against the one ledger
  dateToleranceDays: number;
  amountTolerance: number;
  toleranceType: ToleranceType;
  descriptionThreshold: number;
}

@Injectable({ providedIn: 'root' })
export class Session {
  private readonly http = inject(HttpClient);

  upload(options: UploadOptions): Observable<SessionOut> {
    const formData = new FormData();
    if (options.ledgerFile) {
      formData.append('ledger_file', options.ledgerFile);
    }
    formData.append('use_manual_ledger', String(options.useManualLedger));
    options.bankFiles.forEach((file, index) => {
      formData.append(index === 0 ? 'bank_file' : `bank_file_${index + 1}`, file);
    });
    formData.append('date_tolerance_days', String(options.dateToleranceDays));
    formData.append('amount_tolerance', String(options.amountTolerance));
    formData.append('tolerance_type', options.toleranceType);
    formData.append('description_threshold', String(options.descriptionThreshold));
    return this.http.post<SessionOut>(API_BASE, formData, { withCredentials: true });
  }

  getProgress(sessionId: number): Observable<ProgressOut> {
    return this.http.get<ProgressOut>(`${API_BASE}/${sessionId}/progress`, { withCredentials: true });
  }

  getResults(sessionId: number, page: number, pageSize: number, statusFilter?: string): Observable<ResultsPage> {
    let params = new HttpParams().set('page', page).set('page_size', pageSize);
    if (statusFilter) {
      params = params.set('status_filter', statusFilter);
    }
    return this.http.get<ResultsPage>(`${API_BASE}/${sessionId}/results`, { params, withCredentials: true });
  }

  exportPdfUrl(sessionId: number): string {
    return `${API_BASE}/${sessionId}/export`;
  }

  list(): Observable<SessionOut[]> {
    return this.http.get<SessionOut[]>(API_BASE, { withCredentials: true });
  }

  delete(sessionId: number): Observable<void> {
    return this.http.delete<void>(`${API_BASE}/${sessionId}`, { withCredentials: true });
  }

  searchHistory(filters: HistorySearchFilters): Observable<HistoryMatchOut[]> {
    let params = new HttpParams();
    for (const [key, value] of Object.entries(filters)) {
      if (value !== undefined && value !== null && value !== '') {
        params = params.set(key, String(value));
      }
    }
    return this.http.get<HistoryMatchOut[]>(`${API_BASE}/history/search`, { params, withCredentials: true });
  }
}
