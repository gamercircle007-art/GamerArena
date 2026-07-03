import { Switch } from './switch';
import { Label } from './label';

interface Props {
  checked: boolean;
  onChange: () => void;
  disabled?: boolean;
  label?: string;
}

export default function Toggle({ checked, onChange, disabled, label }: Props) {
  return (
    <div className="flex items-center gap-2">
      <Switch checked={checked} onCheckedChange={onChange} disabled={disabled} aria-label={label} />
      {label && <Label className="text-sm font-normal">{label}</Label>}
    </div>
  );
}