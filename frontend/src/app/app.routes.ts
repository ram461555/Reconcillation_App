import { Routes } from '@angular/router';

import { authGuard } from './core/guards/auth-guard';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'upload' },
  {
    path: 'login',
    loadComponent: () => import('./features/auth/login/login').then((m) => m.Login),
  },
  {
    path: 'register',
    loadComponent: () => import('./features/auth/register/register').then((m) => m.Register),
  },
  {
    path: 'upload',
    canActivate: [authGuard],
    loadComponent: () => import('./features/upload/upload').then((m) => m.Upload),
  },
  {
    path: 'ledger',
    canActivate: [authGuard],
    loadComponent: () => import('./features/ledger/ledger').then((m) => m.Ledger),
  },
  {
    path: 'results/:sessionId',
    canActivate: [authGuard],
    loadComponent: () => import('./features/results/results').then((m) => m.Results),
  },
  {
    path: 'history',
    canActivate: [authGuard],
    loadComponent: () => import('./features/history/history').then((m) => m.History),
  },
  { path: '**', redirectTo: 'upload' },
];
