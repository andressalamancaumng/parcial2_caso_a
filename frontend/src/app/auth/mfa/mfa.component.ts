import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../shared/services/auth.service';

@Component({
  selector: 'app-mfa',
  templateUrl: './mfa.component.html',
  styleUrls: ['./mfa.component.css']
})
export class MfaComponent {
  code = '';
  error = '';
  loading = false;

  constructor(private auth: AuthService, private router: Router) {}

  onVerify() {
    // Validación básica: solo números, 6 dígitos
    if (this.code.length !== 6 || !/^\d+$/.test(this.code)) {
      this.error = 'El código debe tener 6 dígitos numéricos';
      return;
    }

    this.error = '';
    this.loading = true;

    this.auth.verifyMfa(this.code).subscribe({
      next: (res) => {
        // Verificación exitosa: guardamos el token final y redirigimos
        this.auth.saveToken(res.access_token);
        this.auth.clearPartialToken();  // Limpiamos el token parcial (ya no sirve)
        this.router.navigate(['/historia', '']); // o la ruta que corresponda
      },
      error: (err) => {
        if (err.status === 401) {
          this.error = 'Código incorrecto o expirado. Intente de nuevo.';
        } else {
          this.error = 'Error en la verificación. Contacte al administrador.';
        }
        this.loading = false;
      }
    });
  }
}