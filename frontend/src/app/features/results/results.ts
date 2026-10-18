import { Component, computed, inject, signal } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatChipsModule } from '@angular/material/chips';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatIconModule } from '@angular/material/icon';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTableModule } from '@angular/material/table';

import { StatusBadge } from '../../shared/status-badge/status-badge';
import { Session } from '../../core/services/session';
import { MatchResultOut, SummaryOut } from '../../core/models';

type StatusFilter = 'all' | 'Matched' | 'Partial' | 'Missing';

@Component({
  imports: [
    StatusBadge,
    DecimalPipe,
    MatButtonModule,
    MatCardModule,
    MatCheckboxModule,
    MatChipsModule,
    MatExpansionModule,
    MatIconModule,
    MatPaginatorModule,
    MatProgressSpinnerModule,
    MatTableModule,
  ],
  selector: 'app-results',
  styleUrl: './results.scss',
  templateUrl: './results.html',
})
export class Results {
  private readonly route = inject(ActivatedRoute);
  private readonly sessionApi = inject(Session);

  readonly displayedColumns = ['date', 'ledger', 'bank', 'status', 'reason', 'similarity'];
  readonly loading = signal(true);
  readonly errorMessage = signal<string | null>(null);
  readonly summary = signal<SummaryOut | null>(null);
  private readonly allItems = signal<MatchResultOut[]>([]);
  readonly page = signal(0);
  readonly pageSize = signal(25);
  readonly activeFilter = signal<StatusFilter>('all');
  readonly searchTerm = signal('');

  // Advanced filters (Criterion D feedback: more complex search/query options)
  readonly amountDiffMin = signal<number | null>(null);
  readonly dateDiffMin = signal<number | null>(null);
  readonly duplicatesOnly = signal(false);
  readonly toleranceOnly = signal(false);
  readonly dateFrom = signal<string | null>(null);
  readonly dateTo = signal<string | null>(null);

  private sessionId!: number;

  readonly filteredItems = computed(() => {
    const filter = this.activeFilter();
    const term = this.searchTerm().trim().toLowerCase();
    const amountDiffMin = this.amountDiffMin();
    const dateDiffMin = this.dateDiffMin();
    const duplicatesOnly = this.duplicatesOnly();
    const toleranceOnly = this.toleranceOnly();
    const dateFrom = this.dateFrom();
    const dateTo = this.dateTo();

    return this.allItems().filter((item) => {
      if (filter !== 'all' && !item.match_status.startsWith(filter)) return false;

      if (term) {
        const matchesTerm =
          (item.ledger_description ?? '').toLowerCase().includes(term) ||
          (item.bank_narration ?? '').toLowerCase().includes(term) ||
          (item.reason ?? '').toLowerCase().includes(term);
        if (!matchesTerm) return false;
      }

      if (amountDiffMin !== null) {
        if (item.amount_diff === null || Math.abs(item.amount_diff) < amountDiffMin) return false;
      }
      if (dateDiffMin !== null) {
        if (item.date_diff_days === null || Math.abs(item.date_diff_days) < dateDiffMin) return false;
      }
      if (duplicatesOnly && !item.is_duplicate) return false;
      if (toleranceOnly && !item.tolerance_applied) return false;
      if (dateFrom && item.date < dateFrom) return false;
      if (dateTo && item.date > dateTo) return false;

      return true;
    });
  });

  readonly hasAdvancedFilters = computed(
    () =>
      this.amountDiffMin() !== null ||
      this.dateDiffMin() !== null ||
      this.duplicatesOnly() ||
      this.toleranceOnly() ||
      !!this.dateFrom() ||
      !!this.dateTo(),
  );

  readonly pagedItems = computed(() => {
    const start = this.page() * this.pageSize();
    return this.filteredItems().slice(start, start + this.pageSize());
  });

  constructor() {
    this.sessionId = Number(this.route.snapshot.paramMap.get('sessionId'));
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.sessionApi.getResults(this.sessionId, 1, 1000).subscribe({
      next: (result) => {
        this.summary.set(result.summary);
        this.allItems.set(result.items);
        this.loading.set(false);
      },
      error: (err) => {
        this.loading.set(false);
        this.errorMessage.set(err?.error?.detail ?? 'Could not load results.');
      },
    });
  }

  setFilter(filter: StatusFilter): void {
    this.activeFilter.set(filter);
    this.page.set(0);
  }

  onSearch(term: string): void {
    this.searchTerm.set(term);
    this.page.set(0);
  }

  setAmountDiffMin(value: string): void {
    const parsed = value === '' ? null : Number(value);
    this.amountDiffMin.set(parsed !== null && !Number.isNaN(parsed) ? parsed : null);
    this.page.set(0);
  }

  setDateDiffMin(value: string): void {
    const parsed = value === '' ? null : Number(value);
    this.dateDiffMin.set(parsed !== null && !Number.isNaN(parsed) ? parsed : null);
    this.page.set(0);
  }

  toggleDuplicatesOnly(checked: boolean): void {
    this.duplicatesOnly.set(checked);
    this.page.set(0);
  }

  toggleToleranceOnly(checked: boolean): void {
    this.toleranceOnly.set(checked);
    this.page.set(0);
  }

  setDateFrom(value: string): void {
    this.dateFrom.set(value || null);
    this.page.set(0);
  }

  setDateTo(value: string): void {
    this.dateTo.set(value || null);
    this.page.set(0);
  }

  clearAdvancedFilters(): void {
    this.amountDiffMin.set(null);
    this.dateDiffMin.set(null);
    this.duplicatesOnly.set(false);
    this.toleranceOnly.set(false);
    this.dateFrom.set(null);
    this.dateTo.set(null);
    this.page.set(0);
  }

  onPage(event: PageEvent): void {
    this.page.set(event.pageIndex);
    this.pageSize.set(event.pageSize);
  }

  exportUrl(): string {
    return this.sessionApi.exportPdfUrl(this.sessionId);
  }
}
