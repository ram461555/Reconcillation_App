import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTableModule } from '@angular/material/table';

import { LedgerApi } from '../../core/services/ledger';
import { LedgerEntryOut } from '../../core/models';

@Component({
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatCardModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatProgressSpinnerModule,
    MatTableModule,
  ],
  selector: 'app-ledger',
  styleUrl: './ledger.scss',
  templateUrl: './ledger.html',
})
export class Ledger {
  private readonly fb = inject(FormBuilder);
  private readonly ledgerApi = inject(LedgerApi);

  readonly displayedColumns = ['txn_date', 'description', 'amount', 'ref_no', 'actions'];
  readonly loading = signal(true);
  readonly saving = signal(false);
  readonly errorMessage = signal<string | null>(null);
  readonly entries = signal<LedgerEntryOut[]>([]);
  readonly editingId = signal<number | null>(null);

  readonly form = this.fb.nonNullable.group({
    txn_date: ['', Validators.required],
    description: ['', [Validators.required, Validators.maxLength(300)]],
    amount: ['', [Validators.required, Validators.pattern(/^\d+(\.\d{1,2})?$/)]],
    ref_no: [''],
  });

  constructor() {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.ledgerApi.list().subscribe({
      next: (entries) => {
        this.entries.set(entries);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.errorMessage.set('Could not load ledger entries.');
      },
    });
  }

  edit(entry: LedgerEntryOut): void {
    this.editingId.set(entry.id);
    this.form.setValue({
      txn_date: entry.txn_date,
      description: entry.description,
      amount: entry.amount,
      ref_no: entry.ref_no ?? '',
    });
  }

  cancelEdit(): void {
    this.editingId.set(null);
    this.form.reset({ txn_date: '', description: '', amount: '', ref_no: '' });
  }

  submit(): void {
    if (this.form.invalid) {
      return;
    }
    this.saving.set(true);
    this.errorMessage.set(null);
    const raw = this.form.getRawValue();
    const payload = { txn_date: raw.txn_date, description: raw.description, amount: raw.amount, ref_no: raw.ref_no || null };
    const editingId = this.editingId();
    const request = editingId ? this.ledgerApi.update(editingId, payload) : this.ledgerApi.create(payload);
    request.subscribe({
      next: () => {
        this.saving.set(false);
        this.cancelEdit();
        this.load();
      },
      error: (err) => {
        this.saving.set(false);
        this.errorMessage.set(err?.error?.detail ?? 'Could not save ledger entry.');
      },
    });
  }

  remove(entry: LedgerEntryOut): void {
    this.ledgerApi.delete(entry.id).subscribe(() => this.load());
  }
}
