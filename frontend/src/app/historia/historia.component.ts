import * as DOMPurify from 'dompurify';
import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { DomSanitizer } from '@angular/platform-browser';
import { AuthService } from '../shared/services/auth.service';
import { environment } from '../../environments/environment';
import { PdfService } from '../shared/services/pdf.service';

@Component({
  selector: 'app-historia',
  template: `
    <div class="historia-clinica">
      <h2>Historia Clínica — {{ pacienteNombre }}</h2>
      <button (click)="descargarResumenPDF()" class="btn-pdf">
        Descargar resumen PDF
      </button>
      <div [innerHTML]="historiaHtml"></div>
      <!-- Eliminado el enlace que exponía el token -->
      <form (ngSubmit)="agregarNota()">
        <textarea [(ngModel)]="nuevaNota" name="nota"
                  placeholder="Nueva nota clínica"></textarea>
        <button type="submit">Guardar nota</button>
      </form>
    </div>
  `,
  styles: `
  .btn-pdf {
    background-color: #dc3545;
    color: white;
    border: none;
    padding: 8px 16px;
    margin-bottom: 16px;
    border-radius: 4px;
    cursor: pointer;
  }
  .btn-pdf:hover {
    background-color: #c82333;
  }
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
    public auth: AuthService,
    private pdfService: PdfService
  ) {}
  sanitizarHtml(contenido: string): string {
  return DOMPurify.sanitize(contenido);
  }
  ngOnInit() {
    this.cedula = this.route.snapshot.paramMap.get('cedula') || '';
    this.http.get<any>(
      `${environment.apiUrl}/historia/${this.cedula}?auth=${this.auth.token}`
    ).subscribe(resp => {
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
  descargarResumenPDF() {
    this.pdfService.descargarResumenHistoria().subscribe({
      next: (blob: Blob) => {
        // Crear URL temporal para el blob
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'resumen_historia_clinica.pdf';  // Nombre del archivo
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);  // Liberar memoria
      },
      error: (err) => {
        console.error('Error al descargar PDF', err);
        alert('No se pudo generar el PDF. Verifica que tengas permisos.');
      }
    });
  }
}

