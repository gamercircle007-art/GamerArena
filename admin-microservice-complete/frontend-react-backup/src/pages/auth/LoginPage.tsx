import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { AlertCircle, CheckCircle2, Loader2, Shield, Store, UserCog, Crown } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Form, FormControl, FormField, FormItem, FormLabel, FormMessage,
} from '@/components/ui/form';
import AuthLayout from '@/components/auth/AuthLayout';
import PhoneInput from '@/components/auth/PhoneInput';
import OtpInput from '@/components/auth/OtpInput';
import DevQuickLogin from '@/components/auth/DevQuickLogin';
import { authApi } from '@/api/auth.api';
import { useAuthStore } from '@/context/AuthContext';
import { DEV_OTP, DEV_PHONE, USE_MOCK } from '@/mocks/devData';
import type { AuthResponse } from '@/types';
import {
  loginFormSchema, signupFormSchema, otpSchema,
  type LoginFormValues, type SignupFormValues, type OtpFormValues,
} from '@/lib/auth-schemas';
import styles from '@/components/auth/AuthCard.module.scss';
import { cn } from '@/lib/utils';

type Tab = 'login' | 'signup';
type Step = 'form' | 'otp' | 'success';
type AdminRole = 'parlor_owner' | 'admin' | 'super_admin';

const ROLES: { value: AdminRole; label: string; desc: string; icon: typeof Crown; color: string }[] = [
  { value: 'parlor_owner', label: 'Parlor Owner', desc: 'Manage your gaming parlor', icon: Store, color: 'bg-violet-100 text-violet-600' },
  { value: 'admin', label: 'Admin', desc: 'Platform moderation & ops', icon: UserCog, color: 'bg-indigo-100 text-indigo-600' },
  { value: 'super_admin', label: 'Super Admin', desc: 'Full system access', icon: Crown, color: 'bg-amber-100 text-amber-600' },
];

function slugify(name: string) {
  const base = name.trim().toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');
  return (base.match(/^[a-z]/) ? base : `u_${base}`).slice(0, 30) || 'admin_user';
}

export default function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuthStore();

  const [tab, setTab] = useState<Tab>('login');
  const [step, setStep] = useState<Step>('form');
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState('');
  const [countdown, setCountdown] = useState(0);
  const [otpDigits, setOtpDigits] = useState(['', '', '', '', '', '']);

  const loginForm = useForm<LoginFormValues>({
    resolver: zodResolver(loginFormSchema),
    defaultValues: { phone: USE_MOCK ? DEV_PHONE : '' },
  });

  const signupForm = useForm<SignupFormValues>({
    resolver: zodResolver(signupFormSchema),
    defaultValues: { name: '', email: '', phone: USE_MOCK ? DEV_PHONE : '', role: 'admin' },
  });

  const otpForm = useForm<OtpFormValues>({
    resolver: zodResolver(otpSchema),
    defaultValues: { otp: '', password: '' },
  });

  const phone = tab === 'login' ? loginForm.watch('phone') : signupForm.watch('phone');

  const resetFlow = (nextTab: Tab) => {
    setTab(nextTab);
    setStep('form');
    setApiError('');
    setOtpDigits(['', '', '', '', '', '']);
    otpForm.reset();
    if (nextTab === 'login') loginForm.reset({ phone: USE_MOCK ? DEV_PHONE : '' });
    else signupForm.reset({ name: '', email: '', phone: USE_MOCK ? DEV_PHONE : '', role: 'admin' });
  };

  const startCountdown = () => {
    setCountdown(60);
    const t = setInterval(() => setCountdown(c => {
      if (c <= 1) { clearInterval(t); return 0; }
      return c - 1;
    }), 1000);
  };

  const finishAuth = (data: AuthResponse, selectedRole?: AdminRole) => {
    const userRole = data.user.role ?? selectedRole;
    if (userRole === 'user' || !userRole) {
      setApiError('You do not have admin access');
      return;
    }
    login(data.user, { access_token: data.access_token, refresh_token: data.refresh_token });
    setStep('success');
    setTimeout(() => {
      navigate(userRole === 'parlor_owner' ? '/owner' : '/dashboard');
      toast.success(`Welcome, ${data.user.name}!`);
    }, 800);
  };

  const sendOtp = async () => {
    setApiError('');
    const valid = tab === 'login' ? await loginForm.trigger() : await signupForm.trigger();
    if (!valid) return;

    setLoading(true);
    try {
      const fullPhone = `+91${phone.replace(/\D/g, '')}`;
      if (tab === 'login') {
        await authApi.sendOtp(fullPhone);
      } else {
        const { name, email } = signupForm.getValues();
        const username = slugify(name);
        await authApi.signupRequestOtp({
          name: name.trim(),
          username,
          email: email?.trim() || `${username}@gameconnect.local`,
          phone_number: fullPhone,
        });
      }
      setStep('otp');
      if (USE_MOCK) {
        setOtpDigits(DEV_OTP.split(''));
        otpForm.setValue('otp', DEV_OTP);
      }
      startCountdown();
      toast.success(USE_MOCK ? `OTP sent — use ${DEV_OTP}` : 'OTP sent to your phone');
    } catch {
      setApiError('Failed to send OTP. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const verifyOtp = otpForm.handleSubmit(async ({ otp, password }) => {
    setApiError('');
    setLoading(true);
    try {
      const fullPhone = `+91${phone.replace(/\D/g, '')}`;
      if (tab === 'login') {
        const { data } = await authApi.verifyOtp(fullPhone, otp);
        finishAuth(data);
      } else {
        const { role } = signupForm.getValues();
        const { data } = await authApi.signupVerifyOtp(fullPhone, otp, password || 'AdminPass1');
        finishAuth(data, role);
      }
    } catch {
      setApiError('Invalid OTP. Please check and try again.');
    } finally {
      setLoading(false);
    }
  });

  const quickLogin = async (r: AdminRole) => {
    setLoading(true);
    setApiError('');
    try {
      const data = await authApi.devLogin(r);
      finishAuth(data, r);
    } catch {
      setApiError('Quick login failed');
    } finally {
      setLoading(false);
    }
  };

  const syncOtp = (digits: string[]) => {
    setOtpDigits(digits);
    otpForm.setValue('otp', digits.join(''), { shouldValidate: digits.join('').length === 6 });
  };

  return (
    <AuthLayout>
      <div className={styles.card} role="main">
        <div className={styles.tabs} role="tablist" aria-label="Authentication mode">
          <button type="button" role="tab" aria-selected={tab === 'login'}
            className={cn(styles.tab, tab === 'login' && styles.tabActive)} onClick={() => resetFlow('login')}>
            Login
          </button>
          <button type="button" role="tab" aria-selected={tab === 'signup'}
            className={cn(styles.tab, tab === 'signup' && styles.tabActive)} onClick={() => resetFlow('signup')}>
            Sign Up
          </button>
        </div>

        {apiError && (
          <div className={styles.error} role="alert">
            <AlertCircle className="size-4 shrink-0" aria-hidden />
            {apiError}
          </div>
        )}

        {step === 'success' && (
          <div className={styles.success}>
            <div className={styles.successIcon}><CheckCircle2 className="size-6" aria-hidden /></div>
            <p className="font-semibold text-slate-800">Authenticated</p>
            <p className="text-sm text-muted-foreground">Redirecting to dashboard…</p>
            <Loader2 className="size-5 animate-spin text-primary" aria-label="Loading" />
          </div>
        )}

        {step === 'form' && tab === 'login' && (
          <Form {...loginForm}>
            <form onSubmit={e => { e.preventDefault(); sendOtp(); }} className={styles.step}>
              <AuthStepHeader title="Welcome back" subtitle="Sign in with your phone" />
              <FormField control={loginForm.control} name="phone" render={({ field, fieldState }) => (
                <FormItem>
                  <FormControl>
                    <PhoneInput
                      value={field.value}
                      onChange={field.onChange}
                      disabled={loading}
                      error={fieldState.error?.message}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <Button type="submit" disabled={loading} className="w-full mt-5 gc-btn-primary">
                {loading ? <><Loader2 className="size-4 animate-spin" /> Sending…</> : 'Send OTP →'}
              </Button>
            </form>
          </Form>
        )}

        {step === 'form' && tab === 'signup' && (
          <Form {...signupForm}>
            <form onSubmit={e => { e.preventDefault(); sendOtp(); }} className={styles.step}>
              <AuthStepHeader title="Create account" subtitle="Register as an admin user" />
              <div className="space-y-4 mb-4">
                <FormField control={signupForm.control} name="name" render={({ field }) => (
                  <FormItem>
                    <FormLabel>Full Name</FormLabel>
                    <FormControl><Input {...field} placeholder="Manish Kumar" autoComplete="name" /></FormControl>
                    <FormMessage />
                  </FormItem>
                )} />
                <FormField control={signupForm.control} name="email" render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email <span className="text-muted-foreground font-normal">(optional)</span></FormLabel>
                    <FormControl><Input {...field} type="email" placeholder="admin@gameconnect.in" autoComplete="email" /></FormControl>
                    <FormMessage />
                  </FormItem>
                )} />
              </div>
              <FormField control={signupForm.control} name="role" render={({ field }) => (
                <FormItem className="mb-4">
                  <FormLabel>Role</FormLabel>
                  <div className={styles.roleGrid} role="radiogroup" aria-label="Select role">
                    {ROLES.map(r => (
                      <button key={r.value} type="button" role="radio" aria-checked={field.value === r.value}
                        className={cn(styles.roleOption, field.value === r.value && styles.roleActive)}
                        onClick={() => field.onChange(r.value)}>
                        <div className={cn(styles.roleIcon, r.color)}><r.icon className="size-4" aria-hidden /></div>
                        <div>
                          <div className={styles.roleLabel}>{r.label}</div>
                          <div className={styles.roleDesc}>{r.desc}</div>
                        </div>
                      </button>
                    ))}
                  </div>
                  <FormMessage />
                </FormItem>
              )} />
              <FormField control={signupForm.control} name="phone" render={({ field, fieldState }) => (
                <FormItem>
                  <FormControl>
                    <PhoneInput value={field.value} onChange={field.onChange} disabled={loading} error={fieldState.error?.message} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <Button type="submit" disabled={loading} className="w-full mt-5 gc-btn-primary">
                {loading ? <><Loader2 className="size-4 animate-spin" /> Sending…</> : 'Send OTP →'}
              </Button>
            </form>
          </Form>
        )}

        {step === 'otp' && (
          <Form {...otpForm}>
            <form onSubmit={verifyOtp} className={styles.step}>
              <OtpInput value={otpDigits} onChange={syncOtp} phone={phone} disabled={loading} />
              <FormField control={otpForm.control} name="otp" render={() => <FormMessage className="mt-1" />} />

              {tab === 'signup' && !USE_MOCK && (
                <FormField control={otpForm.control} name="password" render={({ field }) => (
                  <FormItem className="mt-4">
                    <FormLabel>Password</FormLabel>
                    <FormControl>
                      <Input {...field} type="password" placeholder="Min 6 chars, upper + lower + digit" autoComplete="new-password" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )} />
              )}

              <Button type="submit" disabled={loading} className="w-full mt-5 gc-btn-primary">
                {loading ? <><Loader2 className="size-4 animate-spin" /> Verifying…</> : 'Verify & Continue'}
              </Button>
              <div className="flex items-center justify-between text-sm mt-3">
                <Button type="button" variant="ghost" size="sm" onClick={() => { setStep('form'); setApiError(''); }} className="h-auto p-0 text-muted-foreground">
                  ← Back
                </Button>
                {countdown > 0 ? (
                  <span className="text-muted-foreground text-xs">Resend in {countdown}s</span>
                ) : (
                  <Button type="button" variant="link" size="sm" onClick={sendOtp} className="h-auto p-0 text-xs">Resend OTP</Button>
                )}
              </div>
            </form>
          </Form>
        )}

        {USE_MOCK && step !== 'success' && <DevQuickLogin loading={loading} onQuickLogin={quickLogin} />}
      </div>
    </AuthLayout>
  );
}

function AuthStepHeader({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="flex items-center gap-3 mb-5">
      <div className="flex size-10 items-center justify-center rounded-xl bg-primary/10">
        <Shield className="size-5 text-primary" aria-hidden />
      </div>
      <div>
        <h2 className="text-lg font-semibold">{title}</h2>
        <p className="text-sm text-muted-foreground">{subtitle}</p>
      </div>
    </div>
  );
}