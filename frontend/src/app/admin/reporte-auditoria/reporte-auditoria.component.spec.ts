import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ReporteAuditoriaComponent } from './reporte-auditoria.component';

describe('ReporteAuditoriaComponent', () => {
  let component: ReporteAuditoriaComponent;
  let fixture: ComponentFixture<ReporteAuditoriaComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ReporteAuditoriaComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(ReporteAuditoriaComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
