import AdminTable from './AdminTable';

interface Props {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  toolbar?: React.ReactNode;
  isError?: boolean;
  onRetry?: () => void;
  errorMessage?: string;
  page?: number;
  pages?: number;
  total?: number;
  onPageChange?: (page: number) => void;
  pageSize?: number;
  className?: string;
}

/** @deprecated Prefer AdminTable — kept for backward compatibility */
export default function TablePanel(props: Props) {
  return <AdminTable {...props} />;
}