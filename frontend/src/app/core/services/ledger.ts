import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { LedgerEntryIn, LedgerEntryOut } from '../models';

const API_BASE = '/api/ledger';

@Injectable({ providedIn: 'root' })
export class LedgerApi {
  private readonly http = inject(HttpClient);

  list(): Observable<LedgerEntryOut[]> {
    return this.http.get<LedgerEntryOut[]>(API_BASE, { withCredentials: true });
  }

  create(entry: LedgerEntryIn): Observable<LedgerEntryOut> {
    return this.http.post<LedgerEntryOut>(API_BASE, entry, { withCredentials: true });
  }

  update(id: number, entry: LedgerEntryIn): Observable<LedgerEntryOut> {
    return this.http.put<LedgerEntryOut>(`${API_BASE}/${id}`, entry, { withCredentials: true });
  }

  delete(id: number): Observable<void> {
    return this.http.delete<void>(`${API_BASE}/${id}`, { withCredentials: true });
  }
}
