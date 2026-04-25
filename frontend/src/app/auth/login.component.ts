import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../shared/services/auth.service';

@Component({
  selector: 'app-login',
  template: `
    <div class="login-container">
      <h2>Clínica Multimedia Salud</h2>
      <form (ngSubmit)="onLogin()">
        <div>
          <label>Email</label>
          <input type="email" [(ngModel)]="email" name="email" required>
        </div>
        <div>
          <label>Contraseña</label>
          <input type="password" [(ngModel)]="password" name="password" required>
        </div>
        <p *ngIf="error" class="error">{{ error }}</p>
        <button type="submit" [disabled]="loading">
          {{ loading ? 'Ingresando...' : 'Ingresar' }}
        </button>
      </form>
    </div>
  `,
  styles: [`
    .login-container {
      max-width: 360px;
      margin: 80px auto;
      padding: 32px;
      background: #fff;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,.12);
    }
    h2 { margin-bottom: 24px; text-align: center; }
    div { margin-bottom: 16px; }
    label { display: block; margin-bottom: 4px; font-size: 14px; }
    input { width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px; }
    button { width: 100%; padding: 10px; background: #1976d2; color: #fff;
             border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
    button:disabled { background: #90caf9; }
    .error { color: #d32f2f; font-size: 13px; margin-bottom: 8px; }
  `]
})
export class LoginComponent {
  email = '';
  password = '';
  error = '';
  loading = false;

  constructor(private auth: AuthService, private router: Router) {}

  onLogin() {
    this.error = '';
    this.loading = true;
    this.auth.login(this.email, this.password).subscribe({
      next: (res) => {
        this.auth.saveToken(res.access_token);
        this.router.navigate(['/historia', '']);
      },
      error: () => {
        this.error = 'Credenciales inválidas';
        this.loading = false;
      }
    });
  }
}
