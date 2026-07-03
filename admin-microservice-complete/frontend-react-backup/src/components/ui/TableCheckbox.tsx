import { Checkbox } from './checkbox';

interface Props {
  checked: boolean;
  onChange: () => void;
  label: string;
}

export default function TableCheckbox({ checked, onChange, label }: Props) {
  return (
    <Checkbox
      checked={checked}
      onCheckedChange={onChange}
      aria-label={label}
    />
  );
}