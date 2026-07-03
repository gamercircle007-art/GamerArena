import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { hasRole } from '../constants/permissions';
import { UserRole } from '../models';
import { AuthService } from '../services/auth.service';

export function roleGuard(requiredRole: UserRole): CanActivateFn {
  return () => {
    const auth = inject(AuthService);
    const router = inject(Router);
    const user = auth.currentUser();

    if (user && hasRole(user.role, requiredRole)) {
      return true;
    }

    return router.createUrlTree(['/unauthorized']);
  };
}