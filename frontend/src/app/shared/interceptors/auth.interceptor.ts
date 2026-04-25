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
    // ← VULNERABLE: adjunta el token sin prefijo "Bearer "
    const token = this.auth.token;
    const authReq = token
      ? req.clone({ setHeaders: { Authorization: token } })
      : req;

    return next.handle(authReq).pipe(
      catchError((err: HttpErrorResponse) => {
        // ← VULNERABLE: sin manejo diferenciado de 401 vs 403
        if (err.status === 401 || err.status === 403) {
          alert(`Error ${err.status}: ${JSON.stringify(err.error)}`);
        }
        return throwError(() => err);
      })
    );
  }
}
