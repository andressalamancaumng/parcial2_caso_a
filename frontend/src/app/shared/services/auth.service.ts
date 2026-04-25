import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class AuthService {
  // ← VULNERABLE: token en variable pública del servicio, leído de localStorage sin verificar exp
  public token: string | null = localStorage.getItem('jwt_clinica');

  constructor(private http: HttpClient, private router: Router) {}

  login(email: string, password: string) {
    return this.http.post<{ access_token: string }>(
      `${environment.apiUrl}/auth/login`, { email, password }
    );
  }

  saveToken(token: string) {
    this.token = token;
    localStorage.setItem('jwt_clinica', token);
  }

  logout() {
    this.token = null;
    localStorage.removeItem('jwt_clinica');
    this.router.navigate(['/login']);
  }

  isAuthenticated(): boolean {
    // ← VULNERABLE: solo verifica que el token existe, no verifica expiración
    return !!this.token;
  }

  getRole(): string {
    if (!this.token) return '';
    try {
      // Decodifica el payload del JWT (base64) — sin verificar la firma
      const payload = JSON.parse(atob(this.token.split('.')[1]));
      return payload.role || '';
    } catch { return ''; }
  }
}
