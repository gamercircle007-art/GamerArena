import { useState } from 'react';
import { toast } from 'sonner';
import {
  PageShell, PageHeader, Card, Button, Input, Select, Toggle,
} from '../../components/ui';
import { cn } from '../../utils/cn';
import { usePermissions } from '../../hooks/usePermissions';
import { PERMISSIONS } from '../../utils/permissions';

type Tab = 'general' | 'features' | 'integrations' | 'security';

const FEATURE_FLAGS = [
  { key: 'parlor_registrations', label: 'Allow new parlor registrations', desc: 'Let businesses sign up as parlor owners' },
  { key: 'paid_tournaments', label: 'Paid tournaments (Razorpay)', desc: 'Enable entry fee collection via Razorpay' },
  { key: 'direct_messaging', label: 'Direct messaging', desc: 'User-to-user chat feature' },
  { key: 'community_posts', label: 'Community posts', desc: 'Forum discussions and guides' },
  { key: 'email_notifications', label: 'Email notifications', desc: 'Transactional emails via SMTP' },
  { key: 'push_notifications', label: 'Push notifications (FCM)', desc: 'Mobile push via Firebase' },
  { key: 'google_signin', label: 'Google Sign-In', desc: 'OAuth login with Google' },
] as const;

const INTEGRATIONS = [
  { name: 'Twilio', key: 'AC••••••••••••4821', status: true, detail: 'SMS OTP delivery' },
  { name: 'Firebase', key: 'credentials.json configured', status: true, detail: 'FCM push notifications' },
  { name: 'Razorpay', key: 'rzp_live_••••••••••••', status: true, detail: 'Test mode' },
  { name: 'AWS S3', key: 'gameconnect-media (ap-south-1)', status: true, detail: 'Media uploads' },
  { name: 'CloudFront', key: 'd1234abcdef.cloudfront.net', status: false, detail: 'CDN distribution' },
] as const;

export default function SettingsPage() {
  const { can, isSuperAdmin } = usePermissions();
  const canEdit = can(PERMISSIONS.MANAGE_SETTINGS);

  const [tab, setTab] = useState<Tab>('general');
  const [maintenance, setMaintenance] = useState(false);
  const [flags, setFlags] = useState<Record<string, boolean>>({
    parlor_registrations: true,
    paid_tournaments: true,
    direct_messaging: true,
    community_posts: true,
    email_notifications: false,
    push_notifications: true,
    google_signin: true,
  });

  const tabs: { key: Tab; label: string }[] = [
    { key: 'general', label: 'General' },
    { key: 'features', label: 'Feature Flags' },
    { key: 'integrations', label: 'Integrations' },
    { key: 'security', label: 'Security' },
  ];

  const toggleFlag = (key: string) => {
    if (!canEdit) return;
    setFlags(prev => ({ ...prev, [key]: !prev[key] }));
    toast.success('Feature flag updated');
  };

  if (!canEdit && !isSuperAdmin) {
    return (
      <PageShell>
        <PageHeader title="Settings" subtitle="Platform configuration" />
        <Card padding className="text-center py-12">
          <p className="text-slate-500">Settings are restricted to super admins.</p>
        </Card>
      </PageShell>
    );
  }

  return (
    <PageShell className="max-w-3xl">
      <PageHeader title="Settings" subtitle="Platform configuration and integrations" />
      <div className="gc-tabs flex-wrap">
        {tabs.map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={tab === t.key ? 'gc-tab-active' : 'gc-tab'}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'general' && (
        <Card padding className="space-y-5">
          <h3 className="gc-section-title">General Settings</h3>
          <div className="grid gap-4">
            <Input label="App Name" defaultValue="GameConnect" disabled={!canEdit} />
            <Input label="Admin Email" defaultValue="admin@gameconnect.in" disabled={!canEdit} />
            <Input label="Support Email" defaultValue="support@gameconnect.in" disabled={!canEdit} />
            <Select label="Timezone" disabled={!canEdit} defaultValue="Asia/Kolkata">
              <option value="Asia/Kolkata">Asia/Kolkata (IST)</option>
              <option value="UTC">UTC</option>
            </Select>
            <div className="flex items-center justify-between py-2 gap-4">
              <div>
                <div className="text-sm font-medium text-slate-700">Maintenance Mode</div>
                <div className="gc-section-subtitle">Block all user access except admins</div>
              </div>
              <Toggle checked={maintenance} onChange={() => canEdit && setMaintenance(m => !m)} disabled={!canEdit} label="Maintenance mode" />
            </div>
          </div>
          {canEdit && (
            <Button onClick={() => toast.success('Settings saved')}>Save Changes</Button>
          )}
        </Card>
      )}

      {tab === 'features' && (
        <Card className="divide-y divide-slate-100">
          {!canEdit && (
            <div className="gc-alert-info m-4">Feature flags are read-only. Only super admins can modify these.</div>
          )}
          {FEATURE_FLAGS.map(f => (
            <div key={f.key} className="flex items-center justify-between px-4 sm:px-6 py-4 gap-4">
              <div className="min-w-0">
                <div className="text-sm font-medium text-slate-700">{f.label}</div>
                <div className="gc-section-subtitle">{f.desc}</div>
              </div>
              <Toggle checked={flags[f.key]} onChange={() => toggleFlag(f.key)} disabled={!canEdit} label={f.label} />
            </div>
          ))}
        </Card>
      )}

      {tab === 'integrations' && (
        <Card className="divide-y divide-slate-100">
          {INTEGRATIONS.map(int => (
            <div key={int.name} className="flex items-center justify-between px-4 sm:px-6 py-4 gap-4">
              <div className="flex items-center gap-3 min-w-0">
                <span className={cn('w-2.5 h-2.5 rounded-full flex-shrink-0', int.status ? 'bg-emerald-500' : 'bg-red-500')} />
                <div className="min-w-0">
                  <div className="text-sm font-medium text-slate-700">{int.name}</div>
                  <div className="text-xs font-mono text-slate-500 truncate">{int.key}</div>
                  <div className="gc-section-subtitle">{int.detail}</div>
                </div>
              </div>
              <span className={cn('text-xs font-medium flex-shrink-0', int.status ? 'text-emerald-600' : 'text-red-600')}>
                {int.status ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          ))}
        </Card>
      )}

      {tab === 'security' && (
        <Card padding className="space-y-5">
          <h3 className="gc-section-title">Security Settings</h3>
          <div className="grid gap-4 sm:grid-cols-2">
            <Input label="Access Token Expiry (mins)" defaultValue="60" type="number" disabled={!canEdit} />
            <Input label="Refresh Token Expiry (days)" defaultValue="30" type="number" disabled={!canEdit} />
            <Input label="OTP per phone / 10 min" defaultValue="3" type="number" disabled={!canEdit} />
            <Input label="Bookings per user / min" defaultValue="5" type="number" disabled={!canEdit} />
          </div>
          <div>
            <label className="gc-label">Admin IP Whitelist</label>
            <textarea
              disabled={!canEdit}
              defaultValue="192.168.1.0/24"
              rows={3}
              placeholder="Comma-separated IPs or CIDR ranges"
              className="gc-textarea font-mono"
            />
          </div>
          {canEdit && (
            <Button onClick={() => toast.success('Security settings saved')}>Save Changes</Button>
          )}
        </Card>
      )}
    </PageShell>
  );
}