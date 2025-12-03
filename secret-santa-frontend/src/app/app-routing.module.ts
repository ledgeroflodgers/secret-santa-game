import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { HomeComponent } from './home/home.component';
import { RegistrationComponent } from './registration/registration.component';
import { ParticipantsComponent } from './participants/participants.component';
import { AdminComponent } from './admin/admin.component';
import { NuclearComponent } from './nuclear/nuclear.component';
import { MobileGiftDisplayComponent } from './mobile-gift-display/mobile-gift-display.component';
import { AdminGuard } from './guards/admin.guard';

const routes: Routes = [
  {
    path: '',
    component: HomeComponent,
    data: { title: '' }
  },
  {
    path: 'register',
    component: RegistrationComponent,
    data: { title: 'Register' }
  },
  {
    path: 'participants',
    component: ParticipantsComponent,
    data: { title: 'Participants' }
  },
  {
    path: 'admin',
    component: AdminComponent,
    canActivate: [AdminGuard],
    data: { title: 'Admin Panel' }
  },
  {
    path: 'mobile-display',
    component: MobileGiftDisplayComponent,
    data: { title: 'Gift Display' }
  },
  {
    path: 'db-refresh',
    component: NuclearComponent,
    data: { title: 'Database Refresh' }
  },
  {
    path: 'game',
    redirectTo: '/admin',
    pathMatch: 'full'
  },
  {
    path: '**',
    redirectTo: '/',
    data: { title: '' }
  }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
