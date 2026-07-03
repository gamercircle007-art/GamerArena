import { Bell, Search, ChevronDown, LogOut, User, KeyRound } from 'lucide-react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList,
  BreadcrumbPage, BreadcrumbSeparator,
} from '@/components/ui/breadcrumb';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { useAuthStore } from '@/context/AuthContext';

const TITLES: Record<string, string> = {
  '/dashboard': 'Dashboard', '/users': 'Users', '/parlors': 'Parlors', '/tournaments': 'Tournaments',
  '/bookings': 'Bookings', '/posts': 'Posts', '/comments': 'Comments', '/events': 'Events',
  '/community': 'Community', '/analytics': 'Analytics', '/roles': 'Roles & Permissions',
  '/notifications': 'Broadcast', '/settings': 'Settings', '/ratings': 'Ratings',
};

export default function TopBar() {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const title = pathname.startsWith('/users/') ? 'User Detail'
    : pathname.startsWith('/parlors/') ? 'Parlor Detail'
    : TITLES[pathname] ?? 'Admin';

  const crumbs = pathname.split('/').filter(Boolean);
  const handleLogout = () => { logout(); navigate('/login'); };

  return (
    <div className="flex flex-1 items-center justify-between gap-3 min-w-0">
      <div className="min-w-0 flex-1">
        <h1 className="text-base sm:text-lg font-semibold tracking-tight text-slate-900 truncate">{title}</h1>
        {crumbs.length > 0 && (
          <Breadcrumb className="hidden sm:block mt-0.5">
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbLink asChild>
                  <Link to="/dashboard" className="text-slate-400 hover:text-indigo-600 transition-colors">Home</Link>
                </BreadcrumbLink>
              </BreadcrumbItem>
              {crumbs.map((c, i) => (
                <span key={i} className="contents">
                  <BreadcrumbSeparator />
                  <BreadcrumbItem>
                    {i < crumbs.length - 1 ? (
                      <BreadcrumbLink asChild>
                        <Link to={'/' + crumbs.slice(0, i + 1).join('/')} className="capitalize text-slate-400 hover:text-indigo-600">
                          {c.length > 20 ? 'detail' : c}
                        </Link>
                      </BreadcrumbLink>
                    ) : (
                      <BreadcrumbPage className="capitalize text-slate-600">{c.length > 20 ? 'detail' : c}</BreadcrumbPage>
                    )}
                  </BreadcrumbItem>
                </span>
              ))}
            </BreadcrumbList>
          </Breadcrumb>
        )}
      </div>

      <div className="flex items-center gap-0.5 sm:gap-1 shrink-0">
        <Button variant="ghost" size="icon" className="hidden lg:flex text-slate-500 hover:text-indigo-600 hover:bg-indigo-50" aria-label="Search">
          <Search className="size-4" />
        </Button>
        <Button variant="ghost" size="icon" className="relative text-slate-500 hover:text-indigo-600 hover:bg-indigo-50" aria-label="Notifications">
          <Bell className="size-4" />
          <span className="absolute top-1.5 right-1.5 size-2 bg-red-500 rounded-full ring-2 ring-background" />
        </Button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="gap-2 px-2 hover:bg-indigo-50">
              <Avatar className="size-8 ring-2 ring-indigo-100">
                <AvatarFallback className="bg-gradient-to-br from-indigo-500 to-violet-600 text-white text-xs font-semibold">
                  {user?.name?.[0]?.toUpperCase() ?? 'A'}
                </AvatarFallback>
              </Avatar>
              <ChevronDown className="size-4 text-slate-400 hidden sm:block" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-52">
            <DropdownMenuLabel>
              <div className="font-medium truncate">{user?.name}</div>
              <div className="text-xs text-muted-foreground font-normal truncate">{user?.email ?? user?.phone}</div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem><User className="size-4 mr-2" /> Profile</DropdownMenuItem>
            <DropdownMenuItem><KeyRound className="size-4 mr-2" /> Change Password</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleLogout} className="text-destructive focus:text-destructive">
              <LogOut className="size-4 mr-2" /> Logout
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}