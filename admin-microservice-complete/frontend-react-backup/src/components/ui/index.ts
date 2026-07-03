// shadcn primitives
export { Button as ShadcnButton, buttonVariants } from './button';
export { Input as ShadcnInput } from './input';
export { Label } from './label';
export { Textarea } from './textarea';
export { Badge } from './badge';
export { Checkbox } from './checkbox';
export { Switch } from './switch';
export { Separator } from './separator';
export { Skeleton as SkeletonPrimitive } from './skeleton';
export { Tabs, TabsList, TabsTrigger, TabsContent } from './tabs';
export {
  Table, TableHeader, TableFooter, TableHead as TableHeadCell, TableCell, TableCaption,
} from './table';
export { Card as ShadcnCard, CardContent, CardHeader as ShadcnCardHeader, CardTitle, CardDescription } from './card';
export {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter,
} from './dialog';
export {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from './alert-dialog';
export {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel,
  DropdownMenuSeparator, DropdownMenuTrigger,
} from './dropdown-menu';
export {
  Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator,
} from './breadcrumb';
export { Avatar, AvatarFallback, AvatarImage } from './avatar';
export { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from './tooltip';
export { Sheet, SheetContent, SheetHeader, SheetTitle } from './sheet';
export {
  Sidebar, SidebarContent, SidebarFooter, SidebarGroup, SidebarGroupContent,
  SidebarGroupLabel, SidebarHeader, SidebarInset, SidebarMenu, SidebarMenuButton,
  SidebarMenuItem, SidebarProvider, SidebarRail, SidebarTrigger, useSidebar,
} from './sidebar';

// Legacy table primitives (sortable headers, muted/actions cells)
export { TableHead, TableBody, TableRow, TableTh, TableTd } from '../app/LegacyTable';

// App wrappers (legacy API)
export { default as Button } from '../app/Button';
export { default as Input } from '../app/Input';
export { default as Select } from '../app/Select';
export { Card, CardHeader, CardBody } from '../app/Card';
export { Skeleton, TableSkeleton, CardSkeleton } from '../app/Skeleton';
export { default as EmptyState } from './EmptyState';
export { default as ErrorBanner } from './ErrorBanner';
export { default as Pagination } from './Pagination';
export { default as FilterBar } from './FilterBar';
export { default as AdminTable } from './AdminTable';
export { default as TablePanel } from './TablePanel';
export { default as DataTable } from './DataTable';
export { default as TableCellUser } from './TableCellUser';
export { default as TableCellActions } from './TableCellActions';
export { default as TableCheckbox } from './TableCheckbox';
export { default as ConfirmModal } from './ConfirmModal';
export { default as StatusBadge } from './StatusBadge';
export { default as StatCard } from './StatCard';
export { default as PageHeader } from './PageHeader';
export { default as DetailHeader } from './DetailHeader';
export { ChartCard, ChartSkeleton } from './ChartCard';
export { default as Toggle } from './Toggle';
export { default as PageShell } from './PageShell';
export { default as SearchInput } from './SearchInput';
export { default as ListPanel } from './ListPanel';
export { default as RankList } from './RankList';