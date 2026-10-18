import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatIconModule } from '@angular/material/icon';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { interval, Subscription, switchMap, takeWhile } from 'rxjs';

import { FileDrop } from '../../shared/file-drop/file-drop';
import { Session } from '../../core/services/session';
import { ToleranceType } from '../../core/models';

const MAX_BANK_FILES = 3;

@Component({
  imports: [
    ReactiveFormsModule,
    RouterLink,
    FileDrop,
    MatButtonModule,
    MatButtonToggleModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatProgressBarModule,
    MatIconModule,
    MatSlideToggleModule,
  ],
  selector: 'app-upload',
  styleUrl: './upload.scss',
  templateUrl: './upload.html',
})
export class Upload {
  private readonly fb = inject(FormBuilder);
  private readonly sessionApi = inject(Session);
  private readonly router = inject(Router);

  readonly ledgerFile = signal<File | null>(null);
  readonly useManualLedger = signal(false);
  // One dropzone per bank statement slot; starts with 1, user can add up to MAX_BANK_FILES.
  readonly bankFileSlots = signal<number[]>([0]);
  readonly bankFiles = signal<(File | null)[]>([null]);
  readonly maxBankFiles = MAX_BANK_FILES;

  readonly submitting = signal(false);
  readonly progressPct = signal(0);
  readonly stage = signal<'idle' | 'uploading' | 'processing' | 'error'>('idle');
  readonly errorMessage = signal<string | null>(null);

  private pollSub?: Subscription;

  readonly form = this.fb.nonNullable.group({
    toleranceType: ['absolute' as ToleranceType, Validators.required],
    dateToleranceDays: [3, [Validators.required, Validators.min(0), Validators.max(365)]],
    amountTolerance: [100, [Validators.required, Validators.min(0)]],
    descriptionThreshold: [80, [Validators.required, Validators.min(0), Validators.max(100)]],
  });

  get canSubmit(): boolean {
    const hasLedger = this.useManualLedger() || !!this.ledgerFile();
    const hasBank = this.bankFiles().some((f) => !!f);
    return hasLedger && hasBank && this.form.valid && !this.submitting();
  }

  toggleManualLedger(useManual: boolean): void {
    this.useManualLedger.set(useManual);
    if (useManual) {
      this.ledgerFile.set(null);
    }
  }

  addBankSlot(): void {
    if (this.bankFileSlots().length >= MAX_BANK_FILES) {
      return;
    }
    this.bankFileSlots.update((slots) => [...slots, slots.length]);
    this.bankFiles.update((files) => [...files, null]);
  }

  removeBankSlot(index: number): void {
    if (this.bankFileSlots().length <= 1) {
      return;
    }
    this.bankFileSlots.update((slots) => slots.slice(0, -1));
    this.bankFiles.update((files) => files.filter((_, i) => i !== index));
  }

  setBankFile(index: number, file: File | null): void {
    this.bankFiles.update((files) => {
      const copy = [...files];
      copy[index] = file;
      return copy;
    });
  }

  submit(): void {
    if (!this.canSubmit) {
      return;
    }

    this.submitting.set(true);
    this.stage.set('uploading');
    this.errorMessage.set(null);
    const { toleranceType, dateToleranceDays, amountTolerance, descriptionThreshold } = this.form.getRawValue();
    const bankFiles = this.bankFiles().filter((f): f is File => !!f);

    this.sessionApi
      .upload({
        ledgerFile: this.useManualLedger() ? null : this.ledgerFile(),
        useManualLedger: this.useManualLedger(),
        bankFiles,
        dateToleranceDays,
        amountTolerance,
        toleranceType,
        descriptionThreshold,
      })
      .subscribe({
        next: (session) => {
          this.stage.set('processing');
          this.pollProgress(session.id);
        },
        error: (err) => {
          this.submitting.set(false);
          this.stage.set('error');
          this.errorMessage.set(err?.error?.detail ?? 'Upload failed.');
        },
      });
  }

  private pollProgress(sessionId: number): void {
    this.pollSub = interval(700)
      .pipe(
        switchMap(() => this.sessionApi.getProgress(sessionId)),
        takeWhile((p) => p.status === 'pending' || p.status === 'processing', true),
      )
      .subscribe({
        next: (p) => {
          this.progressPct.set(p.progress_pct);
          if (p.status === 'done') {
            this.router.navigate(['/results', sessionId]);
          } else if (p.status === 'error') {
            this.submitting.set(false);
            this.stage.set('error');
            this.errorMessage.set(p.error_message ?? 'Reconciliation failed.');
          }
        },
        error: () => {
          this.submitting.set(false);
          this.stage.set('error');
          this.errorMessage.set('Lost connection while processing.');
        },
      });
  }

  ngOnDestroy(): void {
    this.pollSub?.unsubscribe();
  }
}
