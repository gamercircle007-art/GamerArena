import { FlaskConical } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { DEV_OTP, DEV_PHONE } from '@/mocks/devData';
import styles from './DevQuickLogin.module.scss';

interface Props {
  loading?: boolean;
  onQuickLogin: (role: 'super_admin' | 'admin' | 'parlor_owner') => void;
}

export default function DevQuickLogin({ loading, onQuickLogin }: Props) {
  return (
    <details className={styles.wrap}>
      <summary className={styles.summary}>
        <FlaskConical className="size-3.5" aria-hidden />
        Dev quick login
      </summary>
      <div className={styles.body}>
        <p className={styles.hint}>
          Phone <code>{DEV_PHONE}</code> · OTP <code>{DEV_OTP}</code>
        </p>
        <div className={styles.btns}>
          <Button size="sm" variant="outline" onClick={() => onQuickLogin('super_admin')} disabled={loading}>
            Super Admin
          </Button>
          <Button size="sm" variant="outline" onClick={() => onQuickLogin('admin')} disabled={loading}>
            Admin
          </Button>
          <Button size="sm" variant="outline" onClick={() => onQuickLogin('parlor_owner')} disabled={loading}>
            Parlor Owner
          </Button>
        </div>
      </div>
    </details>
  );
}