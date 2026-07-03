import { useMemo, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Send, Users, Store, Globe, Bell, Smartphone, History } from 'lucide-react';
import { toast } from 'sonner';
import {
  PageShell, PageHeader, Button, Select, DataTable,
  Tabs, TabsList, TabsTrigger, TabsContent,
  ShadcnInput as Input, Label, Textarea,
} from '@/components/ui';
import { cn } from '@/lib/utils';
import { adminApi } from '@/api/admin.api';
import { getNotificationHistoryColumns } from '../_shared/listColumns';

type Target = 'all' | 'users' | 'parlor_owners';
type NType = 'info' | 'alert' | 'promotion' | 'event';

const TARGETS: { value: Target; label: string; Icon: React.ElementType; desc: string; color: string }[] = [
  { value: 'all', label: 'Everyone', Icon: Globe, desc: 'All active users', color: 'bg-indigo-50 border-indigo-300 text-indigo-700' },
  { value: 'users', label: 'Gamers only', Icon: Users, desc: 'Regular user accounts', color: 'bg-emerald-50 border-emerald-300 text-emerald-700' },
  { value: 'parlor_owners', label: 'Parlor Owners', Icon: Store, desc: 'Business accounts', color: 'bg-violet-50 border-violet-300 text-violet-700' },
];

const TYPES: { value: NType; label: string; icon: string }[] = [
  { value: 'info', label: 'Info', icon: 'ℹ️' },
  { value: 'alert', label: 'Alert', icon: '⚠️' },
  { value: 'promotion', label: 'Promo', icon: '🎁' },
  { value: 'event', label: 'Event', icon: '🎮' },
];

export default function NotificationsPage() {
  const [tab, setTab] = useState('send');
  const [target, setTarget] = useState<Target>('all');
  const [ntype, setNtype] = useState<NType>('info');
  const [histType, setHistType] = useState('');
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [result, setResult] = useState<{ sent_to: number } | null>(null);

  const { data: history, isLoading: histLoading } = useQuery({
    queryKey: ['notification-history', histType],
    queryFn: () => adminApi.getNotificationHistory({ ...(histType ? { type: histType } : {}) }),
    enabled: tab === 'history',
  });

  const { mutate, isPending } = useMutation({
    mutationFn: () => adminApi.broadcast({ title, body, target, type: ntype }),
    onSuccess: (data) => { setResult(data); toast.success(`Sent to ${data.sent_to} users!`); setTitle(''); setBody(''); },
    onError: () => toast.error('Failed to send'),
  });

  const historyColumns = useMemo(() => getNotificationHistoryColumns(), []);
  const canSend = title.trim().length > 0 && body.trim().length > 0;

  return (
    <PageShell className="max-w-4xl">
      <PageHeader title="Broadcast" subtitle="Send push notifications to platform users" />

      <Tabs value={tab} onValueChange={setTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="send" className="gap-1.5"><Send className="size-3.5" /> Send Broadcast</TabsTrigger>
          <TabsTrigger value="history" className="gap-1.5"><History className="size-3.5" /> History</TabsTrigger>
        </TabsList>

        <TabsContent value="history" className="space-y-4">
          <FilterRow>
            <Select value={histType} onChange={e => setHistType(e.target.value)}>
              <option value="">All types</option>
              {TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
            </Select>
          </FilterRow>
          <DataTable
            title="Broadcast History"
            subtitle={`${history?.items.length ?? 0} broadcasts`}
            columns={historyColumns}
            data={history?.items ?? []}
            isLoading={histLoading}
            emptyMessage="No broadcast history"
          />
        </TabsContent>

        <TabsContent value="send">
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 sm:gap-6">
            <div className="lg:col-span-3 space-y-4 sm:space-y-5">
              <div className="gc-card-flat p-5">
                <h3 className="gc-section-title mb-3">Target Audience</h3>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {TARGETS.map(t => (
                    <button key={t.value} type="button" onClick={() => setTarget(t.value)}
                      className={cn('gc-choice-card', target === t.value ? cn('gc-choice-card-active', t.color) : 'gc-choice-card-inactive')}>
                      <t.Icon className="size-5" />
                      <div className="text-xs font-semibold">{t.label}</div>
                      <div className="text-xs opacity-70">{t.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              <div className="gc-card-flat p-5">
                <h3 className="gc-section-title mb-3">Notification Type</h3>
                <div className="flex flex-wrap gap-2">
                  {TYPES.map(t => (
                    <Button key={t.value} variant={ntype === t.value ? 'primary' : 'secondary'} size="sm" onClick={() => setNtype(t.value)} className="text-xs">
                      {t.icon} {t.label}
                    </Button>
                  ))}
                </div>
              </div>

              <div className="gc-card-flat p-5 space-y-4">
                <h3 className="gc-section-title">Message Content</h3>
                <div className="space-y-2">
                  <Label htmlFor="title">Title <span className="text-destructive">*</span></Label>
                  <Input id="title" value={title} onChange={e => setTitle(e.target.value)} maxLength={80} placeholder="e.g. New Feature Alert! 🎮" />
                  <div className="text-right text-xs text-muted-foreground">{title.length}/80</div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="body">Message <span className="text-destructive">*</span></Label>
                  <Textarea id="body" value={body} onChange={e => setBody(e.target.value)} rows={4} maxLength={500}
                    placeholder="Write your message here..." />
                  <div className="text-right text-xs text-muted-foreground">{body.length}/500</div>
                </div>
                <Button onClick={() => mutate()} disabled={!canSend} loading={isPending} className="w-full gc-btn-primary">
                  <Send size={16} /> Send Notification
                </Button>
              </div>

              {result && (
                <div className="gc-alert-success">
                  <div className="size-10 shrink-0 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center">✓</div>
                  <div>
                    <div className="font-semibold">Notification Sent!</div>
                    <div className="text-emerald-600 text-sm">Delivered to {result.sent_to} users</div>
                  </div>
                </div>
              )}
            </div>

            <div className="lg:col-span-2">
              <div className="gc-card-flat p-5 sticky top-4">
                <h3 className="gc-section-title mb-4">Preview</h3>
                <div className="flex items-center justify-center">
                  <div className="w-full max-w-[16rem] bg-slate-900 rounded-3xl p-4 shadow-xl">
                    <div className="bg-slate-800 rounded-2xl p-3 text-white">
                      <div className="flex items-center gap-2 mb-2">
                        <div className="w-6 h-6 bg-indigo-500 rounded-lg flex items-center justify-center"><Bell size={12} /></div>
                        <span className="text-xs font-medium">GameConnect</span>
                        <span className="text-xs text-slate-400 ml-auto">now</span>
                      </div>
                      <div className="text-xs font-semibold mb-1">{title || 'Your notification title here'}</div>
                      <div className="text-xs text-slate-300 leading-relaxed">{body || 'Your message content will appear here.'}</div>
                    </div>
                    <div className="flex justify-center mt-3"><Smartphone size={12} className="text-slate-600" /></div>
                  </div>
                </div>
                <p className="mt-4 text-xs text-muted-foreground text-center">Preview on Android/iOS</p>
              </div>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </PageShell>
  );
}

function FilterRow({ children }: { children: React.ReactNode }) {
  return <div className="gc-card-flat p-4 flex flex-wrap gap-2">{children}</div>;
}