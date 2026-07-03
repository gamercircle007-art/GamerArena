import { Outlet } from 'react-router-dom';
import { SidebarInset, SidebarProvider, SidebarTrigger } from '@/components/ui/sidebar';
import { Separator } from '@/components/ui/separator';
import { TooltipProvider } from '@/components/ui/tooltip';
import AppSidebar from '@/components/layout/AppSidebar';
import TopBar from '@/components/layout/TopBar';

/** Main admin shell: sidebar + glass topbar + scrollable content */
export default function AdminLayout() {
  return (
    <TooltipProvider delayDuration={0}>
      <SidebarProvider defaultOpen>
        <AppSidebar />
        <SidebarInset className="flex flex-col min-h-svh overflow-hidden">
          <header className="gc-glass-header">
            <SidebarTrigger className="-ml-1 text-slate-500 hover:text-indigo-600 hover:bg-indigo-50" />
            <Separator orientation="vertical" className="mr-2 h-4 hidden sm:block bg-slate-200" />
            <TopBar />
          </header>
          <main className="gc-main">
            <Outlet />
          </main>
        </SidebarInset>
      </SidebarProvider>
    </TooltipProvider>
  );
}