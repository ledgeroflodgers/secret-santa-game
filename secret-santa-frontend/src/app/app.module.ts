import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule } from '@angular/common/http';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { HomeComponent } from './home/home.component';
import { RegistrationComponent } from './registration/registration.component';
import { ParticipantsComponent } from './participants/participants.component';
import { AdminComponent } from './admin/admin.component';
import { NuclearComponent } from './nuclear/nuclear.component';
import { NavigationComponent } from './navigation/navigation.component';
import { LoadingComponent } from './shared/loading/loading.component';
import { ErrorDisplayComponent } from './shared/error-display/error-display.component';
import { MobileGiftDisplayComponent } from './mobile-gift-display/mobile-gift-display.component';

@NgModule({
  declarations: [
    AppComponent,
    HomeComponent,
    RegistrationComponent,
    ParticipantsComponent,
    AdminComponent,
    NuclearComponent,
    NavigationComponent,
    LoadingComponent,
    ErrorDisplayComponent,
    MobileGiftDisplayComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    HttpClientModule,
    FormsModule,
    ReactiveFormsModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
