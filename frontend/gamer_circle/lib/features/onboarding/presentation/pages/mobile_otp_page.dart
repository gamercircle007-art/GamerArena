import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/constants/app_constants.dart';
import 'package:gamer_circle/core/constants/onboarding_colors.dart';
import 'package:gamer_circle/features/auth/presentation/providers/login_otp_providers.dart';
import 'package:gamer_circle/features/auth/presentation/providers/login_otp_state.dart';
import 'package:gamer_circle/features/auth/presentation/widgets/otp_input_widget.dart';
import 'package:gamer_circle/features/onboarding/presentation/widgets/onboarding_primary_button.dart';

class MobileOtpPage extends ConsumerStatefulWidget {
  const MobileOtpPage({super.key, required this.phone});

  final String phone;

  @override
  ConsumerState<MobileOtpPage> createState() => _MobileOtpPageState();
}

class _MobileOtpPageState extends ConsumerState<MobileOtpPage> {
  String _otp = '';
  int _secondsLeft = 0;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _startResendTimer();
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  void _startResendTimer() {
    _timer?.cancel();
    setState(() => _secondsLeft = 60);
    _timer = Timer.periodic(const Duration(seconds: 1), (t) {
      if (_secondsLeft == 0) {
        t.cancel();
      } else {
        setState(() => _secondsLeft--);
      }
    });
  }

  String get _maskedPhone {
    final phone = widget.phone;
    if (phone.length < 4) return phone;
    return '${'*' * (phone.length - 4)}${phone.substring(phone.length - 4)}';
  }

  @override
  Widget build(BuildContext context) {
    ref.listen<LoginOtpState>(loginOtpNotifierProvider, (prev, next) {
      if (next is LoginOtpError) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(next.message),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    });

    final otpState = ref.watch(loginOtpNotifierProvider);
    final isVerifying = otpState is LoginOtpVerifying;

    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 8),
              Align(
                alignment: Alignment.centerLeft,
                child: IconButton(
                  onPressed: () => context.go('/mobile-number'),
                  icon: const Icon(Icons.arrow_back_ios_new, size: 20),
                  color: OnboardingColors.textPrimary,
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
                ),
              ),
              const SizedBox(height: 40),
              const Text(
                'Verify OTP',
                style: TextStyle(
                  fontSize: 26,
                  fontWeight: FontWeight.w800,
                  color: OnboardingColors.textPrimary,
                ),
              ),
              const SizedBox(height: 8),
              RichText(
                text: TextSpan(
                  text: 'Code sent to ',
                  style: const TextStyle(
                    fontSize: 15,
                    color: OnboardingColors.textSecondary,
                  ),
                  children: [
                    TextSpan(
                      text: _maskedPhone,
                      style: const TextStyle(
                        fontWeight: FontWeight.w700,
                        color: OnboardingColors.textPrimary,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 32),
              OtpInputWidget(
                onChanged: (otp) => setState(() => _otp = otp),
                onCompleted: (otp) => setState(() => _otp = otp),
              ),
              const SizedBox(height: 16),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  TextButton(
                    onPressed: () => context.go('/mobile-number'),
                    child: const Text(
                      'Change number',
                      style: TextStyle(
                        color: OnboardingColors.primary,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  _secondsLeft > 0
                      ? Text(
                          'Resend in ${_secondsLeft}s',
                          style: const TextStyle(
                            color: OnboardingColors.textSecondary,
                            fontSize: 13,
                          ),
                        )
                      : TextButton(
                          onPressed: () {
                            ref
                                .read(loginOtpNotifierProvider.notifier)
                                .requestOtp(widget.phone);
                            _startResendTimer();
                          },
                          child: const Text(
                            'Resend OTP',
                            style: TextStyle(
                              color: OnboardingColors.primary,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ),
                ],
              ),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: OnboardingColors.permissionIconBg,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  'Dev mode — OTP is: ${AppConstants.devOtpBypass}',
                  style: const TextStyle(
                    color: OnboardingColors.primary,
                    fontSize: 13,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
              const Spacer(),
              OnboardingPrimaryButton(
                label: 'Verify & Continue',
                enabled: _otp.length == 6,
                isLoading: isVerifying,
                onPressed: _otp.length == 6 && !isVerifying
                    ? () => ref
                        .read(loginOtpNotifierProvider.notifier)
                        .verifyOtp(_otp)
                    : null,
              ),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }
}