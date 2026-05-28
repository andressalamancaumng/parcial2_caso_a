import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';

import { AppComponent } from './app.component';
import { HistoriaComponent } from './historia/historia.component';
import { LoginComponent } from './auth/login.component';
import { MfaComponent } from './auth/mfa/mfa.component'; 
import { AuthInterceptor } from './shared/interceptors/auth.interceptor';
import { AuthGuard } from './shared/guards/auth.guard';
import { OrdenMedicaComponent } from './medico/orden-medica/orden-medica.component';
import { ReporteAuditoriaComponent } from './admin/reporte-auditoria/reporte-auditoria.component';

const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { path: 'mfa', component: MfaComponent },           // <-- AÑADE ESTA RUTA
  { path: 'historia/:cedula', component: HistoriaComponent, canActivate: [AuthGuard] },
  { path: 'orden-medica', component: OrdenMedicaComponent, canActivate: [AuthGuard] },
  { path: 'reporte-auditoria', component: ReporteAuditoriaComponent, canActivate: [AuthGuard] },
  { path: '**', redirectTo: '/login' }
];

@NgModule({
  declarations: [AppComponent, HistoriaComponent, LoginComponent, MfaComponent, OrdenMedicaComponent, ReporteAuditoriaComponent], 
  imports: [
    BrowserModule,
    HttpClientModule,
    FormsModule,
    ReactiveFormsModule,
    RouterModule.forRoot(routes)
  ],
  providers: [
    { provide: HTTP_INTERCEPTORS, useClass: AuthInterceptor, multi: true }
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }