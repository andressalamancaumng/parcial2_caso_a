import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class PdfService {

  constructor(private http: HttpClient) { }

  /**
   * HU-A08: Descargar resumen de historia clínica (para paciente autenticado)
   * El backend debe obtener el ID del paciente desde el token JWT,
   * no desde un parámetro de la URL.
   */
  descargarResumenHistoria(): Observable<Blob> {
    // Llamada sin parámetros; el backend sabe quién es por el token
    return this.http.get(`${environment.apiUrl}/pacientes/historia/resumen.pdf`, {
      responseType: 'blob'
    });
  }

  /**
   * HU-A09: Generar orden médica para un paciente asignado al médico.
   * Se necesita el ID del paciente y de la atención (opcional).
   * El backend debe validar que el médico tenga asignado a ese paciente.
   */
  generarOrdenMedica(pacienteId: string, atencionId?: string): Observable<Blob> {
    let url = `${environment.apiUrl}/medicos/ordenes?pacienteId=${pacienteId}`;
    if (atencionId) {
      url += `&atencionId=${atencionId}`;
    }
    return this.http.get(url, {
      responseType: 'blob'
    });
  }

  /**
   * HU-A10: Reporte de auditoría (solo admin o auditor)
   * Recibe rango de fechas en formato YYYY-MM-DD.
   */
  reporteAuditoria(fechaInicio: string, fechaFin: string): Observable<Blob> {
    return this.http.get(`${environment.apiUrl}/admin/reporte-accesos`, {
      params: { fechaInicio, fechaFin },
      responseType: 'blob'
    });
  }
}