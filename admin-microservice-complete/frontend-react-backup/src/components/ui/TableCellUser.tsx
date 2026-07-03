import { cn } from '../../utils/cn';

interface Props {
  name: string;
  subtitle?: string;
  avatar?: React.ReactNode;
  imageUrl?: string;
  initials?: string;
  avatarColor?: string;
  square?: boolean;
}

export default function TableCellUser({
  name, subtitle, avatar, imageUrl, initials, avatarColor = 'bg-indigo-100 text-indigo-600', square,
}: Props) {
  const letter = initials ?? name?.[0]?.toUpperCase() ?? '?';

  return (
    <div className="gc-table-avatar-cell">
      {avatar ?? (
        imageUrl ? (
          <img src={imageUrl} alt="" className={square ? 'gc-table-avatar-square object-cover' : 'gc-table-avatar-img'} />
        ) : (
          <div className={cn(square ? 'gc-table-avatar-square' : 'gc-table-avatar', avatarColor)}>
            {letter}
          </div>
        )
      )}
      <div className="min-w-0">
        <div className="gc-table-cell-primary truncate">{name}</div>
        {subtitle && <div className="gc-table-cell-sub">{subtitle}</div>}
      </div>
    </div>
  );
}