import { ComponentFixture, TestBed } from '@angular/core/testing';

import { OrdenMedicaComponent } from './orden-medica.component';

describe('OrdenMedicaComponent', () => {
  let component: OrdenMedicaComponent;
  let fixture: ComponentFixture<OrdenMedicaComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [OrdenMedicaComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(OrdenMedicaComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
