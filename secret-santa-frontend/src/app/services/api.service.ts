import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private readonly baseUrl = `${environment.apiUrl}/api`;

  constructor(private http: HttpClient) { }

  // Health check endpoint
  healthCheck(): Observable<any> {
    return this.http.get(`${this.baseUrl}/health`);
  }

  // Placeholder methods for future implementation
  getParticipants(): Observable<any> {
    return this.http.get(`${this.baseUrl}/participants`);
  }

  addParticipant(participant: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/participants`, participant);
  }

  getGameState(): Observable<any> {
    return this.http.get(`${this.baseUrl}/game-state`);
  }
}
