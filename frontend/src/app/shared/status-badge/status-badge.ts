import { Component, computed, input } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';

import { MatchStatus } from '../../core/models';

@Component({
  imports: [MatIconModule, MatTooltipModule],
  selector: 'app-status-badge',
  styleUrl: './status-badge.scss',
  templateUrl: './status-badge.html',
})
export class StatusBadge {
  readonly status = input.required<MatchStatus>();
  readonly isDuplicate = input(false);

  protected readonly cssClass = computed(() => {
    switch (this.status()) {
      case 'Matched':
      case 'Matched (tolerance)':
        return 'status-matched';
      case 'Partial':
        return 'status-partial';
      default:
        return 'status-missing';
    }
  });
}
