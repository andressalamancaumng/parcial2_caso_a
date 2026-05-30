import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { environment } from '../../../environments/environment';
import { Observable, throwError } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class AuthService {
  // Token final (para acceder a los endpoints protegidos)
  public token: string | null = localStorage.getItem('jwt_clinica');
  
  // Token parcial (para el segundo factor MFA)
  private partialToken: string | null = null;

  constructor(private http: HttpClient, private router: Router) {}

  // 1. Login: ahora espera una respuesta que puede tener mfa_required y partial_token
  login(email: string, password: string): Observable<any> {
    return this.http.post(`${environment.apiUrl}/auth/login`, { email, password });
  }

  // 2. Guardar token parcial (después de validar credenciales)
  savePartialToken(token: string): void {
    this.partialToken = token;
    // Usamos sessionStorage para que se borre al cerrar la pestaña
    sessionStorage.setItem('partial_token', token);
  }

  // 3. Obtener token parcial
  getPartialToken(): string | null {
    if (!this.partialToken) {
      this.partialToken = sessionStorage.getItem('partial_token');
    }
    return this.partialToken;
  }

  // 4. Limpiar token parcial
  clearPartialToken(): void {
    this.partialToken = null;
    sessionStorage.removeItem('partial_token');
  }

  // 5. Verificar el código MFA (segundo factor)
  verifyMfa(code: string): Observable<{ access_token: string }> {
    const partial = this.getPartialToken();
    if (!partial) {
      // Si no hay token parcial, lanzamos un error observable
      return throwError(() => new Error('No hay sesión MFA activa. Inicie sesión nuevamente.'));
    }
    // Enviamos el código en el body y el token parcial en el header Authorization
    return this.http.post<{ access_token: string }>(
      `${environment.apiUrl}/auth/mfa/verify`,
      { code },
      { headers: { Authorization: `Bearer ${partial}` } }
    );
  }

  // 6. Guardar token final (igual que antes)
  saveToken(token: string): void {
    this.token = token;
    localStorage.setItem('jwt_clinica', token);
  }

  // 7. Logout
  logout(): void {
    this.token = null;
    this.clearPartialToken();  // también limpiamos el parcial
    localStorage.removeItem('jwt_clinica');
    this.router.navigate(['/login']);
  }

  // 8. Verifica si hay token final (para el guard)
  isAuthenticated(): boolean {
    return !!this.token;
  }

  // 9. Obtener rol desde el token (útil para mostrar/ocultar botones)
  getRole(): string {
    if (!this.token) return '';
    try {
      const payload = JSON.parse(atob(this.token.split('.')[1]));
      return payload.role || '';
    } catch {
      return '';
    }
  }
}