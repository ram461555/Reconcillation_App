import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Observable, tap } from 'rxjs';

import { UserOut } from '../models';

const API_BASE = '/api/auth';

@Injectable({ providedIn: 'root' })
export class Auth {
  private readonly http = inject(HttpClient);

  private readonly _currentUser = signal<UserOut | null>(null);
  private readonly _initialized = signal(false);

  readonly currentUser = this._currentUser.asReadonly();
  readonly isAuthenticated = computed(() => this._currentUser() !== null);
  readonly initialized = this._initialized.asReadonly();

  register(username: string, email: string, password: string): Observable<UserOut> {
    return this.http.post<UserOut>(`${API_BASE}/register`, { username, email, password });
  }

  login(username: string, password: string): Observable<UserOut> {
    return this.http
      .post<UserOut>(`${API_BASE}/login`, { username, password }, { withCredentials: true })
      .pipe(tap((user) => this._currentUser.set(user)));
  }

  logout(): Observable<void> {
    return this.http
      .post<void>(`${API_BASE}/logout`, {}, { withCredentials: true })
      .pipe(tap(() => this._currentUser.set(null)));
  }

  /** Called once at app startup to check for an existing session cookie. */
  fetchCurrentUser(): Observable<UserOut> {
    return this.http
      .get<UserOut>(`${API_BASE}/me`, { withCredentials: true })
      .pipe(tap((user) => this._currentUser.set(user)));
  }

  clearSession(): void {
    this._currentUser.set(null);
  }

  markInitialized(): void {
    this._initialized.set(true);
  }
}
