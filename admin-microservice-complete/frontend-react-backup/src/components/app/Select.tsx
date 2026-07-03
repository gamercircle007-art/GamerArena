import React from 'react';
import { Label } from '@/components/ui/label';
import {
  Select as ShadcnSelect, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import { cn } from '@/lib/utils';

interface OptionProps {
  value: string;
  children: React.ReactNode;
}

interface Props {
  label?: string;
  value?: string;
  defaultValue?: string;
  onChange?: (e: { target: { value: string } }) => void;
  onValueChange?: (value: string) => void;
  disabled?: boolean;
  className?: string;
  children: React.ReactNode;
}

function collectOptions(children: React.ReactNode): { value: string; label: string }[] {
  const options: { value: string; label: string }[] = [];
  React.Children.forEach(children, child => {
    if (React.isValidElement<OptionProps>(child) && child.type === 'option') {
      options.push({ value: child.props.value, label: String(child.props.children) });
    }
  });
  return options;
}

export default function Select({ label, value, defaultValue, onChange, onValueChange, disabled, className, children }: Props) {
  const options = collectOptions(children);
  const handleChange = (v: string) => {
    onValueChange?.(v);
    onChange?.({ target: { value: v } });
  };

  return (
    <div className={cn('space-y-1.5', className)}>
      {label && <Label>{label}</Label>}
      <ShadcnSelect value={value} defaultValue={defaultValue} onValueChange={handleChange} disabled={disabled}>
        <SelectTrigger>
          <SelectValue placeholder={label ?? 'Select...'} />
        </SelectTrigger>
        <SelectContent>
          {options.map(o => (
            <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
          ))}
        </SelectContent>
      </ShadcnSelect>
    </div>
  );
}