import { Gamepad2 } from 'lucide-react';
import styles from './AuthLayout.module.scss';

interface Props {
  children: React.ReactNode;
}

export default function AuthLayout({ children }: Props) {
  return (
    <div className={styles.page}>
      <div className={styles.grid} aria-hidden />
      <div className={styles.content}>
        <div className={styles.brand}>
          <div className={styles.logo}>
            <Gamepad2 className="size-6" aria-hidden />
          </div>
          <div>
            <h1 className={styles.brandTitle}>GameConnect</h1>
            <p className={styles.brandSub}>Admin Control Panel</p>
          </div>
        </div>
        {children}
        <p className={styles.footer}>Secure access for authorized administrators only</p>
      </div>
    </div>
  );
}