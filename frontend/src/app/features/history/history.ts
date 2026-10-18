import { Component, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatTableModule } from '@angular/material/table';

import { StatusBadge } from '../../shared/status-badge/status-badge';
import { Session } from '../../core/services/session';
import { HistoryMatchOut, SessionOut } from '../../core/models';

@Component({
  imports: [
    RouterLink,
    DatePipe,
    ReactiveFormsModule,
    StatusBadge,
    MatButtonModule,
    MatCardModule,
    MatCheckboxModule,
    MatExpansionModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatProgressSpinnerModule,
    MatSelectModule,
    MatTableModule,
  ],
  selector: 'app-history',
  styleUrl: './history.scss',
  templateUrl: './history.html',
})
export class History {
  private readonly fb = inject(FormBuilder);
  private readonly sessionApi = inject(Session);
  private readonly router = inject(Router);

  readonly displayedColumns = ['created_at', 'ledger_filename', 'bank_filename', 'tolerance', 'status', 'actions'];
  readonly searchColumns = ['session_created_at', 'date', 'ledger_description', 'bank_narration', 'match_status', 'amount_diff', 'date_diff_days', 'view'];

  readonly loading = signal(true);
  readonly sessions = signal<SessionOut[]>([]);
  readonly errorMessage = signal<string | null>(null);

  readonly searching = signal(false);
  readonly searchErrorMessage = signal<string | null>(null);
  readonly searchResults = signal<HistoryMatchOut[] | null>(null);

  readonly searchForm = this.fb.group({
    dateFrom: [''],
    dateTo: [''],
    amountDiffMin: [''],
    dateDiffMin: [''],
    statusFilter: [''],
    duplicatesOnly: [false],
    toleranceOnly: [false],
  });

  constructor() {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.sessionApi.list().subscribe({
      next: (sessions) => {
        this.sessions.set(sessions);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.errorMessage.set('Could not load history.');
      },
    });
  }

  runSearch(): void {
    const raw = this.searchForm.getRawValue();
    this.searching.set(true);
    this.searchErrorMessage.set(null);
    this.sessionApi
      .searchHistory({
        date_from: raw.dateFrom || undefined,
        date_to: raw.dateTo || undefined,
        amount_diff_min: raw.amountDiffMin ? Number(raw.amountDiffMin) : undefined,
        date_diff_min: raw.dateDiffMin ? Number(raw.dateDiffMin) : undefined,
        status_filter: raw.statusFilter || undefined,
        duplicates_only: raw.duplicatesOnly || undefined,
        tolerance_only: raw.toleranceOnly || undefined,
      })
      .subscribe({
        next: (results) => {
          this.searching.set(false);
          this.searchResults.set(results);
        },
        error: () => {
          this.searching.set(false);
          this.searchErrorMessage.set('Search failed. Please try again.');
        },
      });
  }

  clearSearch(): void {
    this.searchForm.reset({
      dateFrom: '',
      dateTo: '',
      amountDiffMin: '',
      dateDiffMin: '',
      statusFilter: '',
      duplicatesOnly: false,
      toleranceOnly: false,
    });
    this.searchResults.set(null);
  }

  open(session: SessionOut): void {
    this.router.navigate(['/results', session.id]);
  }

  remove(session: SessionOut, event: Event): void {
    event.stopPropagation();
    this.sessionApi.delete(session.id).subscribe(() => this.load());
  }
}
