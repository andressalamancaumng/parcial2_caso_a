import { Component } from '@angular/core';
import { PdfService } from '../../shared/services/pdf.service';

@Component({
  selector: 'app-orden-medica',
  standalone: true,
  imports: [],
  templateUrl: './orden-medica.component.html',
  styleUrl: './orden-medica.component.css'
})
export class OrdenMedicaComponent {
  pacienteId = '';
  atencionId = '';
  loading = false;
  mensaje = '';

  constructor(private pdfService: PdfService) {}

  generarOrden() {
    if (!this.pacienteId) {
      this.mensaje = 'Debe ingresar el ID del paciente.';
      return;
    }
    this.loading = true;
    this.mensaje = '';

    this.pdfService.generarOrdenMedica(this.pacienteId, this.atencionId || undefined)
      .subscribe({
        next: (blob) => {
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `orden_medica_paciente_${this.pacienteId}.pdf`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          window.URL.revokeObjectURL(url);
          this.loading = false;
        },
        error: (err) => {
          console.error(err);
          this.mensaje = 'Error al generar la orden. Verifica que el paciente esté asignado a ti.';
          this.loading = false;
        }
      });
  }
}
