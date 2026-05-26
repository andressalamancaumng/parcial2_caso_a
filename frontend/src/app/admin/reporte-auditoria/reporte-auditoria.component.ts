import { Component } from '@angular/core';
import { PdfService } from '../../shared/services/pdf.service';

@Component({
  selector: 'app-reporte-auditoria',
  templateUrl: './reporte-auditoria.component.html',
  styleUrls: ['./reporte-auditoria.component.css']
})
export class ReporteAuditoriaComponent {
  fechaInicio = '';
  fechaFin = '';
  loading = false;
  mensaje = '';

  constructor(private pdfService: PdfService) {}

  generarReporte() {
    if (!this.fechaInicio || !this.fechaFin) {
      this.mensaje = 'Debe seleccionar ambas fechas.';
      return;
    }
    // Validación simple: fecha inicio no puede ser mayor que fecha fin
    if (this.fechaInicio > this.fechaFin) {
      this.mensaje = 'La fecha de inicio no puede ser mayor que la fecha de fin.';
      return;
    }
    this.loading = true;
    this.mensaje = '';

    this.pdfService.reporteAuditoria(this.fechaInicio, this.fechaFin)
      .subscribe({
        next: (blob) => {
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `reporte_auditoria_${this.fechaInicio}_a_${this.fechaFin}.pdf`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          window.URL.revokeObjectURL(url);
          this.loading = false;
        },
        error: (err) => {
          console.error(err);
          this.mensaje = 'Error al generar el reporte. Verifica que tengas permisos de administrador.';
          this.loading = false;
        }
      });
  }
}