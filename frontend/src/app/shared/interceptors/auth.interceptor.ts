import { Injectable } from '@angular/core';
import {
  HttpInterceptor, HttpRequest, HttpHandler, HttpEvent, HttpErrorResponse
} from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { AuthService } from '../services/auth.service';
import { Router } from '@angular/router';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  constructor(private auth: AuthService, private router: Router) {}

  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    // Obtener el token del servicio de autenticación
    const token = this.auth.token;

    // Si hay token, clonamos la petición y añadimos el header Authorization con prefijo "Bearer "
    let authReq = req;
    if (token) {
      authReq = req.clone({
        setHeaders: { Authorization: `Bearer ${token}` }
      });
    }

    // Continuamos con la petición (modificada o no) y manejamos errores
    return next.handle(authReq).pipe(
      catchError((error: HttpErrorResponse) => {
        if (error.status === 401) {
          // Token inválido o expirado: limpiar token, redirigir al login y mostrar mensaje
          this.auth.logout();   // Limpia localStorage y token
          this.router.navigate(['/login']);
          alert('Sesión expirada. Por favor, inicie sesión nuevamente.');
        } 
        else if (error.status === 403) {
          // Usuario no autorizado para esta acción: solo mostrar mensaje, no redirigir
          alert('No tienes permiso para realizar esta acción.');
        }
        // Propagar el error para que el componente también lo maneje si quiere
        return throwError(() => error);
      })
    );
  }
}
