import * as DOMPurify from 'dompurify';
import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { DomSanitizer } from '@angular/platform-browser';
import { AuthService } from '../shared/services/auth.service';
import { environment } from '../../environments/environment';

@Component({
  selector: 'app-historia',
  template: `
    <div class="historia-clinica">
      <h2>Historia Clínica — {{ pacienteNombre }}</h2>

      <!-- ← VULNERABLE: renderiza HTML del servidor sin sanitizar — XSS -->
      <div [innerHTML]="historiaHtml"></div>

      <!-- ← VULNERABLE: token JWT expuesto en la URL -->
      <a [href]="'/historia/' + cedula + '?token=' + auth.token">
        Compartir con otro médico
      </a>

      <form (ngSubmit)="agregarNota()">
        <textarea [(ngModel)]="nuevaNota" name="nota"
                  placeholder="Nueva nota clínica"></textarea>
        <!-- ← Sin longitud máxima ni validación del contenido -->
        <button type="submit">Guardar nota</button>
      </form>
    </div>
  `
})
export class HistoriaComponent implements OnInit {
  pacienteNombre = '';
  historiaHtml: any = '';   // any en lugar de SafeHtml
  cedula = '';
  nuevaNota = '';

  constructor(
    private route: ActivatedRoute,
    private http: HttpClient,
    private sanitizer: DomSanitizer,
    public auth: AuthService
  ) {}
  sanitizarHtml(contenido: string): string {
  return DOMPurify.sanitize(contenido);
  }
  ngOnInit() {
    this.cedula = this.route.snapshot.paramMap.get('cedula') || '';

    // ← VULNERABLE: token en query param en lugar de header (manejado por interceptor)
    this.http.get<any>(
      `${environment.apiUrl}/historia/${this.cedula}?auth=${this.auth.token}`
    ).subscribe(resp => {
      // ← VULNERABLE: bypassea la sanitización de Angular
      const htmlLimpio = this.sanitizarHtml(resp.contenido_html);
      this.historiaHtml = this.sanitizer.bypassSecurityTrustHtml(htmlLimpio);
      this.pacienteNombre = resp.paciente_nombre;
    });
  }

  agregarNota() {
    this.http.post(
      `${environment.apiUrl}/historia/${this.cedula}/nota`,
      { contenido: this.nuevaNota, token: this.auth.token }  // ← token en body
    ).subscribe(() => this.nuevaNota = '');
  }
}
