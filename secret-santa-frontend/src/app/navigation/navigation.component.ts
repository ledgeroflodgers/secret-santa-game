import { Component, OnInit } from '@angular/core';
import { NavigationService, NavigationItem } from '../services/navigation.service';
import { Observable } from 'rxjs';

@Component({
  selector: 'app-navigation',
  templateUrl: './navigation.component.html',
  styleUrls: ['./navigation.component.css']
})
export class NavigationComponent implements OnInit {
  navigationItems: NavigationItem[] = [];
  currentPageTitle$: Observable<string>;

  constructor(private navigationService: NavigationService) {
    this.currentPageTitle$ = this.navigationService.currentPageTitle$;
  }

  ngOnInit(): void {
    this.navigationItems = this.navigationService.navigationItems;
  }

  isCurrentRoute(path: string): boolean {
    return this.navigationService.isCurrentRoute(path);
  }

  onNavigate(path: string): void {
    // The routerLink will handle navigation, but we could add analytics here
    console.log(`Navigating to: ${path}`);
  }
}
