// src/utils/permissions.ts — RBAC: single source of truth
export const ROLES = { SUPER_ADMIN:'super_admin', ADMIN:'admin', PARLOR_OWNER:'parlor_owner', USER:'user' } as const;
export type Role = typeof ROLES[keyof typeof ROLES];

export const PERMISSIONS = {
  VIEW_USERS:'view_users', CREATE_USERS:'create_users', EDIT_USERS:'edit_users',
  DELETE_USERS:'delete_users', BAN_USERS:'ban_users', CHANGE_ROLE:'change_role',
  VIEW_PARLORS:'view_parlors', VERIFY_PARLORS:'verify_parlors', EDIT_PARLORS:'edit_parlors', DELETE_PARLORS:'delete_parlors',
  VIEW_POSTS:'view_posts', DELETE_POSTS:'delete_posts',
  VIEW_COMMENTS:'view_comments', DELETE_COMMENTS:'delete_comments',
  VIEW_COMMUNITY:'view_community', DELETE_COMMUNITY:'delete_community', PIN_COMMUNITY:'pin_community',
  VIEW_TOURNAMENTS:'view_tournaments', EDIT_TOURNAMENTS:'edit_tournaments', DELETE_TOURNAMENTS:'delete_tournaments',
  VIEW_ALL_BOOKINGS:'view_all_bookings', VIEW_OWN_BOOKINGS:'view_own_bookings',
  VIEW_EVENTS:'view_events', EDIT_EVENTS:'edit_events', DELETE_EVENTS:'delete_events',
  VIEW_PLATFORM_ANALYTICS:'view_platform_analytics', VIEW_OWN_ANALYTICS:'view_own_analytics', VIEW_REVENUE:'view_revenue',
  VIEW_RATINGS:'view_ratings', DELETE_RATINGS:'delete_ratings',
  SEND_BROADCAST:'send_broadcast',
  MANAGE_ROLES:'manage_roles', VIEW_ROLES:'view_roles', MANAGE_SETTINGS:'manage_settings',
} as const;
export type Permission = typeof PERMISSIONS[keyof typeof PERMISSIONS];

const ALL = Object.values(PERMISSIONS) as Permission[];

export const ROLE_PERMISSIONS: Record<Role, Permission[]> = {
  super_admin: ALL,
  admin: [
    'view_users','edit_users','ban_users','delete_users',
    'view_parlors','verify_parlors','edit_parlors','delete_parlors',
    'view_posts','delete_posts','view_comments','delete_comments',
    'view_community','delete_community','pin_community',
    'view_tournaments','edit_tournaments','delete_tournaments',
    'view_all_bookings','view_events','edit_events','delete_events',
    'view_platform_analytics','view_revenue','view_ratings','delete_ratings',
    'send_broadcast','view_roles',
  ],
  parlor_owner: ['view_own_analytics','view_own_bookings','view_events'],
  user: [],
};

export const hasPermission = (role: Role|undefined, perm: Permission) =>
  role ? (ROLE_PERMISSIONS[role]?.includes(perm) ?? false) : false;

export const hasAnyPermission = (role: Role|undefined, perms: Permission[]) =>
  perms.some(p => hasPermission(role, p));

export const canAccessAdmin = (role: Role|undefined) =>
  role === 'super_admin' || role === 'admin' || role === 'parlor_owner';

export const ROLE_META: Record<Role, {label:string; color:string; bg:string; desc:string}> = {
  super_admin:  {label:'Super Admin',  color:'text-red-600',   bg:'bg-red-50',    desc:'Full unrestricted access'},
  admin:        {label:'Admin',        color:'text-indigo-600',bg:'bg-indigo-50', desc:'Manage users, content, analytics'},
  parlor_owner: {label:'Parlor Owner', color:'text-violet-600',bg:'bg-violet-50', desc:'Own parlor analytics & events'},
  user:         {label:'User',         color:'text-slate-600', bg:'bg-slate-100', desc:'No admin access'},
};

export const PERMISSION_GROUPS = [
  { label:'Users', perms:[
    {key:'view_users'    as Permission, label:'View Users',     desc:'See all accounts'},
    {key:'edit_users'    as Permission, label:'Edit Users',     desc:'Update profiles'},
    {key:'ban_users'     as Permission, label:'Ban/Unban',      desc:'Restrict user login'},
    {key:'delete_users'  as Permission, label:'Delete Users',   desc:'Remove accounts permanently'},
    {key:'change_role'   as Permission, label:'Change Role',    desc:'Assign admin roles (super_admin only)'},
  ]},
  { label:'Parlors', perms:[
    {key:'view_parlors'   as Permission, label:'View Parlors',   desc:'Browse all parlors'},
    {key:'verify_parlors' as Permission, label:'Verify Parlors', desc:'Grant verification badge'},
    {key:'edit_parlors'   as Permission, label:'Edit Parlors',   desc:'Modify parlor details'},
    {key:'delete_parlors' as Permission, label:'Delete Parlors', desc:'Remove parlor and all data'},
  ]},
  { label:'Content', perms:[
    {key:'view_posts'      as Permission, label:'View Posts',    desc:'See all social posts'},
    {key:'delete_posts'    as Permission, label:'Delete Posts',  desc:'Remove posts'},
    {key:'delete_comments' as Permission, label:'Delete Comments',desc:'Remove comments'},
    {key:'delete_community'as Permission, label:'Delete Community',desc:'Remove community posts'},
    {key:'pin_community'   as Permission, label:'Pin Posts',     desc:'Pin to top of community'},
  ]},
  { label:'Tournaments & Bookings', perms:[
    {key:'view_tournaments'  as Permission, label:'View Tournaments', desc:'See all tournaments'},
    {key:'edit_tournaments'  as Permission, label:'Edit Status',      desc:'Change tournament status'},
    {key:'delete_tournaments'as Permission, label:'Delete',           desc:'Remove tournament'},
    {key:'view_all_bookings' as Permission, label:'All Bookings',     desc:'See every booking'},
    {key:'view_events'       as Permission, label:'View Events',      desc:'See all events'},
    {key:'delete_events'     as Permission, label:'Delete Events',    desc:'Remove events'},
  ]},
  { label:'Analytics', perms:[
    {key:'view_platform_analytics'as Permission, label:'Platform Analytics', desc:'All charts & growth data'},
    {key:'view_own_analytics'     as Permission, label:'Own Analytics',      desc:'Own parlor data only'},
    {key:'view_revenue'           as Permission, label:'Revenue Data',       desc:'Financial reports'},
  ]},
  { label:'System', perms:[
    {key:'send_broadcast'  as Permission, label:'Send Broadcast',   desc:'Push to all users'},
    {key:'view_roles'      as Permission, label:'View Roles',       desc:'See role config'},
    {key:'manage_roles'    as Permission, label:'Manage Roles',     desc:'Edit permissions (super_admin)'},
    {key:'manage_settings' as Permission, label:'Settings',         desc:'Platform config (super_admin)'},
  ]},
];
