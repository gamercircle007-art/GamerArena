import { z } from 'zod';

export const phoneSchema = z
  .string()
  .min(10, 'Enter a valid 10-digit phone number')
  .max(10, 'Phone must be 10 digits')
  .regex(/^\d{10}$/, 'Phone must contain only digits');

export const loginFormSchema = z.object({
  phone: phoneSchema,
});

export const signupFormSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters').max(100),
  email: z.union([z.string().email('Invalid email'), z.literal('')]).optional(),
  phone: phoneSchema,
  role: z.enum(['parlor_owner', 'admin', 'super_admin']),
});

export const otpSchema = z.object({
  otp: z.string().length(6, 'Enter the full 6-digit OTP').regex(/^\d{6}$/, 'OTP must be numeric'),
  password: z
    .string()
    .optional()
    .refine(
      v => !v || /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{6,128}$/.test(v),
      'Password needs upper, lower, and a digit (min 6 chars)',
    ),
});

export type LoginFormValues = z.infer<typeof loginFormSchema>;
export type SignupFormValues = z.infer<typeof signupFormSchema>;
export type OtpFormValues = z.infer<typeof otpSchema>;