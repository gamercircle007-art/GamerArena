import { UserRole } from '../models';

export const ROLES = {
  SUPER_ADMIN: 'super_admin',
  ADMIN: 'admin',
  PARLOR_OWNER: 'parlor_owner',
  USER: 'user',
} as const;

export const PERMISSIONS = {
  VIEW_USERS: 'view_users',
  BAN_USERS: 'ban_users',
  DELETE_USERS: 'delete_users',
  VIEW_PARLORS: 'view_parlors',
  VERIFY_PARLORS: 'verify_parlors',
  MANAGE_PARLORS: 'manage_parlors',
  DELETE_PARLORS: 'delete_parlors',
  VIEW_POSTS: 'view_posts',
  DELETE_POSTS: 'delete_posts',
  MODERATE_COMMENTS: 'moderate_comments',
  VIEW_TOURNAMENTS: 'view_tournaments',
  MANAGE_TOURNAMENTS: 'manage_tournaments',
  VIEW_ALL_BOOKINGS: 'view_all_bookings',
  VIEW_EVENTS: 'view_events',
  VIEW_COMMUNITY: 'view_community',
  VIEW_PLATFORM_ANALYTICS: 'view_platform_analytics',
  SEND_BROADCAST: 'send_broadcast',
  VIEW_RATINGS: 'view_ratings',
  VIEW_GEO: 'view_geo',
  VIEW_LIKES: 'view_likes',
  VIEW_COMMENTS: 'view_comments',
  MANAGE_ROLES: 'manage_roles',
  MANAGE_SETTINGS: 'manage_settings',
} as const;

export type Permission = (typeof PERMISSIONS)[keyof typeof PERMISSIONS];

export const ROLE_PERMISSIONS: Record<UserRole, string[]> = {
  super_admin: ['*'],
  admin: [
    PERMISSIONS.VIEW_USERS,
    PERMISSIONS.BAN_USERS,
    PERMISSIONS.DELETE_USERS,
    PERMISSIONS.VIEW_PARLORS,
    PERMISSIONS.VERIFY_PARLORS,
    PERMISSIONS.MANAGE_PARLORS,
    PERMISSIONS.DELETE_PARLORS,
    PERMISSIONS.VIEW_POSTS,
    PERMISSIONS.DELETE_POSTS,
    PERMISSIONS.MODERATE_COMMENTS,
    PERMISSIONS.VIEW_TOURNAMENTS,
    PERMISSIONS.MANAGE_TOURNAMENTS,
    PERMISSIONS.VIEW_ALL_BOOKINGS,
    PERMISSIONS.VIEW_EVENTS,
    PERMISSIONS.VIEW_COMMUNITY,
    PERMISSIONS.VIEW_PLATFORM_ANALYTICS,
    PERMISSIONS.SEND_BROADCAST,
    PERMISSIONS.VIEW_RATINGS,
    PERMISSIONS.VIEW_GEO,
    PERMISSIONS.VIEW_LIKES,
    PERMISSIONS.VIEW_COMMENTS,
  ],
  parlor_owner: ['view_own_analytics', 'view_own_bookings'],
  user: [],
};

const ADMIN_ROLES: UserRole[] = ['admin', 'super_admin'];

export function hasPermission(role: UserRole, permission: string): boolean {
  const perms = ROLE_PERMISSIONS[role] ?? [];
  return perms.includes('*') || perms.includes(permission);
}

export function canAccessAdmin(role: UserRole): boolean {
  return ADMIN_ROLES.includes(role);
}

export function hasRole(userRole: UserRole, requiredRole: UserRole): boolean {
  if (requiredRole === ROLES.SUPER_ADMIN) {
    return userRole === ROLES.SUPER_ADMIN;
  }
  if (requiredRole === ROLES.ADMIN) {
    return userRole === ROLES.ADMIN || userRole === ROLES.SUPER_ADMIN;
  }
  return userRole === requiredRole;
}