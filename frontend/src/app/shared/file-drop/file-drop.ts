import { Component, input, output, signal } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';

const MAX_SIZE_BYTES = 10 * 1024 * 1024;

@Component({
  imports: [MatIconModule],
  selector: 'app-file-drop',
  styleUrl: './file-drop.scss',
  templateUrl: './file-drop.html',
})
export class FileDrop {
  readonly label = input('Drag PDF here or click to browse');
  readonly fileSelected = output<File | null>();

  protected readonly selectedFile = signal<File | null>(null);
  protected readonly dragOver = signal(false);
  protected readonly errorMessage = signal<string | null>(null);

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    this.dragOver.set(true);
  }

  onDragLeave(): void {
    this.dragOver.set(false);
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    this.dragOver.set(false);
    const file = event.dataTransfer?.files?.[0] ?? null;
    this.handleFile(file);
  }

  onFileInputChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.handleFile(input.files?.[0] ?? null);
  }

  clear(): void {
    this.selectedFile.set(null);
    this.errorMessage.set(null);
    this.fileSelected.emit(null);
  }

  private handleFile(file: File | null): void {
    if (!file) {
      return;
    }
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      this.errorMessage.set('Only PDF files are supported.');
      this.selectedFile.set(null);
      this.fileSelected.emit(null);
      return;
    }
    if (file.size === 0) {
      this.errorMessage.set('File is empty.');
      this.selectedFile.set(null);
      this.fileSelected.emit(null);
      return;
    }
    if (file.size > MAX_SIZE_BYTES) {
      this.errorMessage.set('File is too large (max 10MB).');
      this.selectedFile.set(null);
      this.fileSelected.emit(null);
      return;
    }
    this.errorMessage.set(null);
    this.selectedFile.set(file);
    this.fileSelected.emit(file);
  }

  formatSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }
}
