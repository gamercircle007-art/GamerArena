import { ArrowLeft } from 'lucide-react';
import Button from '@/components/app/Button';
import { cn } from '../../utils/cn';

interface Props {
  onBack: () => void;
  title: string;
  subtitle?: string;
  badge?: React.ReactNode;
  avatar?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
}

export default function DetailHeader({ onBack, title, subtitle, badge, avatar, actions, className }: Props) {
  return (
    <div className={cn('flex items-center justify-between flex-wrap gap-3', className)}>
      <div className="flex items-center gap-3 min-w-0">
        <Button variant="icon" onClick={onBack} aria-label="Go back" className="border border-slate-200">
          <ArrowLeft size={16} />
        </Button>
        {avatar}
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h2 className="text-lg font-semibold text-slate-800 truncate">{title}</h2>
            {badge}
          </div>
          {subtitle && <p className="text-xs text-slate-400 truncate">{subtitle}</p>}
        </div>
      </div>
      {actions && <div className="flex items-center gap-2 flex-wrap">{actions}</div>}
    </div>
  );
}