import { Search } from 'lucide-react';
import { Input } from './input';
import { cn } from '@/lib/utils';

interface Props extends React.InputHTMLAttributes<HTMLInputElement> {
  className?: string;
}

export default function SearchInput({ className, ...props }: Props) {
  return (
    <div className={cn('relative flex-1 min-w-[12rem] max-w-md', className)}>
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground pointer-events-none" />
      <Input className="pl-9" {...props} />
    </div>
  );
}