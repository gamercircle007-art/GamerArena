import { Outlet, useNavigate } from 'react-router-dom';
import { Gamepad2, LogOut, Store } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { useAuthStore } from '../../context/AuthContext';

export default function OwnerLayout() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => { logout(); navigate('/login'); };

  return (
    <div className="min-h-svh bg-muted/30">
      <header className="sticky top-0 z-40 border-b bg-background">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-violet-600">
              <Gamepad2 className="size-[18px] text-white" aria-hidden />
            </div>
            <div className="min-w-0">
              <div className="truncate text-sm font-bold">GameConnect</div>
              <div className="flex items-center gap-1 text-xs text-violet-600">
                <Store className="size-2.5" aria-hidden /> Parlor Owner
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2 sm:gap-4">
            <span className="hidden max-w-[12rem] truncate text-sm text-muted-foreground sm:block">
              {user?.parlor_name ?? user?.name}
            </span>
            <Separator orientation="vertical" className="hidden h-4 sm:block" />
            <Button variant="ghost" size="sm" onClick={handleLogout} className="text-muted-foreground hover:text-destructive">
              <LogOut className="size-3.5" />
              <span className="hidden sm:inline">Logout</span>
            </Button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-4 sm:py-6">
        <Outlet />
      </main>
    </div>
  );
}