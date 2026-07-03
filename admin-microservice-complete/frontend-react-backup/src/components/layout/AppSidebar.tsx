import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, Users, Store, Trophy, Ticket, FileText, MessageSquare,
  Calendar, Globe, BarChart3, ShieldCheck, Bell, Settings, Gamepad2, Star, LogOut,
} from 'lucide-react';
import {
  Sidebar, SidebarContent, SidebarFooter, SidebarGroup, SidebarGroupContent,
  SidebarGroupLabel, SidebarHeader, SidebarMenu, SidebarMenuButton, SidebarMenuItem,
  SidebarRail,
} from '@/components/ui/sidebar';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { useAuthStore } from '@/context/AuthContext';
import { usePermissions } from '@/hooks/usePermissions';
import { PERMISSIONS, ROLE_META, type Permission } from '@/utils/permissions';
import { cn } from '@/lib/utils';

interface NavItem {
  to: string;
  icon: React.ElementType;
  label: string;
  permission?: Permission;
  superAdminOnly?: boolean;
}

const NAV: { section: string; items: NavItem[] }[] = [
  { section: 'Overview', items: [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/analytics', icon: BarChart3, label: 'Analytics', permission: PERMISSIONS.VIEW_PLATFORM_ANALYTICS },
  ]},
  { section: 'Management', items: [
    { to: '/users', icon: Users, label: 'Users', permission: PERMISSIONS.VIEW_USERS },
    { to: '/parlors', icon: Store, label: 'Parlors', permission: PERMISSIONS.VIEW_PARLORS },
    { to: '/tournaments', icon: Trophy, label: 'Tournaments', permission: PERMISSIONS.VIEW_TOURNAMENTS },
    { to: '/bookings', icon: Ticket, label: 'Bookings', permission: PERMISSIONS.VIEW_ALL_BOOKINGS },
    { to: '/events', icon: Calendar, label: 'Events', permission: PERMISSIONS.VIEW_EVENTS },
  ]},
  { section: 'Content', items: [
    { to: '/posts', icon: FileText, label: 'Posts', permission: PERMISSIONS.VIEW_POSTS },
    { to: '/comments', icon: MessageSquare, label: 'Comments', permission: PERMISSIONS.VIEW_COMMENTS },
    { to: '/community', icon: Globe, label: 'Community', permission: PERMISSIONS.VIEW_COMMUNITY },
    { to: '/ratings', icon: Star, label: 'Ratings', permission: PERMISSIONS.VIEW_RATINGS },
  ]},
  { section: 'System', items: [
    { to: '/notifications', icon: Bell, label: 'Broadcast', permission: PERMISSIONS.SEND_BROADCAST },
    { to: '/roles', icon: ShieldCheck, label: 'Roles & Perms', superAdminOnly: true },
    { to: '/settings', icon: Settings, label: 'Settings', superAdminOnly: true },
  ]},
];

export default function AppSidebar() {
  const { user, logout } = useAuthStore();
  const { can, isSuperAdmin } = usePermissions();
  const navigate = useNavigate();
  const roleMeta = user ? ROLE_META[user.role] : null;

  const handleLogout = () => { logout(); navigate('/login'); };

  return (
    <Sidebar collapsible="icon" className="border-r border-sidebar-border bg-sidebar">
      <SidebarHeader className="border-b border-sidebar-border/80 px-2 py-3">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" className="pointer-events-none hover:bg-transparent">
              <div className="flex aspect-square size-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-lg shadow-indigo-500/20">
                <Gamepad2 className="size-4" />
              </div>
              <div className="grid flex-1 text-left text-sm leading-tight">
                <span className="truncate font-bold tracking-tight">GameConnect</span>
                <span className="truncate text-[11px] text-sidebar-foreground/60">Admin Panel</span>
              </div>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <SidebarContent className="px-1 py-2">
        {NAV.map(({ section, items }) => {
          const visible = items.filter(item => {
            if (item.superAdminOnly && !isSuperAdmin) return false;
            if (item.permission && !can(item.permission)) return false;
            return true;
          });
          if (!visible.length) return null;
          return (
            <SidebarGroup key={section}>
              <SidebarGroupLabel className="text-[10px] uppercase tracking-wider text-sidebar-foreground/40 px-3">
                {section}
              </SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {visible.map(item => (
                    <SidebarMenuItem key={item.to}>
                      <SidebarMenuButton asChild tooltip={item.label}>
                        <NavLink
                          to={item.to}
                          className={({ isActive }) => cn(
                            'rounded-lg transition-all duration-150',
                            isActive && 'gc-nav-active',
                          )}
                        >
                          <item.icon className="size-4 shrink-0" strokeWidth={2} />
                          <span className="truncate">{item.label}</span>
                        </NavLink>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          );
        })}
      </SidebarContent>

      {user && (
        <SidebarFooter className="border-t border-sidebar-border/80 p-2">
          <SidebarMenu>
            <SidebarMenuItem>
              <div className="flex items-center gap-2.5 px-2 py-2 group-data-[collapsible=icon]:justify-center rounded-lg">
                <Avatar className="size-8 ring-2 ring-indigo-500/20">
                  <AvatarFallback className="bg-gradient-to-br from-indigo-500 to-violet-600 text-white text-xs font-semibold">
                    {user.name?.[0]?.toUpperCase() ?? 'A'}
                  </AvatarFallback>
                </Avatar>
                <div className="grid flex-1 text-left text-sm leading-tight group-data-[collapsible=icon]:hidden min-w-0">
                  <span className="truncate font-medium text-sidebar-foreground">{user.name}</span>
                  {roleMeta && (
                    <Badge variant="secondary" className="w-fit text-[10px] px-1.5 py-0 h-4 bg-indigo-500/20 text-indigo-200 border-0">
                      {roleMeta.label}
                    </Badge>
                  )}
                </div>
              </div>
            </SidebarMenuItem>
            <SidebarMenuItem>
              <SidebarMenuButton
                onClick={handleLogout}
                tooltip="Logout"
                className="text-red-400/90 hover:text-red-300 hover:bg-red-500/10 rounded-lg"
              >
                <LogOut className="size-4" />
                <span>Logout</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarFooter>
      )}
      <SidebarRail />
    </Sidebar>
  );
}