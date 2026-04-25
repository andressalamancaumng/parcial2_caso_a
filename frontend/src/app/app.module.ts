import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';

import { AppComponent } from './app.component';
import { HistoriaComponent } from './historia/historia.component';
import { AuthInterceptor } from './shared/interceptors/auth.interceptor';
import { AuthGuard } from './shared/guards/auth.guard';

const routes: Routes = [
  { path: 'historia/:cedula', component: HistoriaComponent, canActivate: [AuthGuard] },
  { path: '**', redirectTo: '/login' }
];

@NgModule({
  declarations: [AppComponent, HistoriaComponent],
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
export class AppModule {}
