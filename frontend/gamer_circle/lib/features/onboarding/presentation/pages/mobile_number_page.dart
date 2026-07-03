import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/constants/onboarding_colors.dart';
import 'package:gamer_circle/app/router/router_notifier.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_providers.dart';
import 'package:gamer_circle/features/auth/presentation/providers/login_otp_providers.dart';
import 'package:gamer_circle/features/auth/presentation/providers/login_otp_state.dart';
import 'package:gamer_circle/features/onboarding/presentation/widgets/continue_as_guest_button.dart';
import 'package:gamer_circle/features/onboarding/presentation/widgets/onboarding_primary_button.dart';

class MobileNumberPage extends ConsumerStatefulWidget {
  const MobileNumberPage({super.key});

  @override
  ConsumerState<MobileNumberPage> createState() => _MobileNumberPageState();
}

class _MobileNumberPageState extends ConsumerState<MobileNumberPage> {
  final _controller = TextEditingController();
  String _countryCode = '+91';

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  bool get _isValid => RegExp(r'^[6-9]\d{9}$').hasMatch(_controller.text);

  String get _fullPhone => '$_countryCode${_controller.text}';

  Future<void> _continueAsGuest() async {
    await ref.read(authNotifierProvider.notifier).continueAsGuest();
    await ref.read(routerNotifierProvider).refreshOnboardingState();
    if (mounted) context.go('/');
  }

  void _onContinue() {
    if (!_isValid) return;
    ref.read(loginOtpNotifierProvider.notifier).requestOtp(_fullPhone);
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
      if (next is LoginOtpSent) {
        context.go('/mobile-otp', extra: next.phone);
      }
    });

    final otpState = ref.watch(loginOtpNotifierProvider);
    final isSending = otpState is LoginOtpSending;

    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 8),
              Row(
                children: [
                  IconButton(
                    onPressed: () => context.go('/onboarding'),
                    icon: const Icon(Icons.arrow_back_ios_new, size: 20),
                    color: OnboardingColors.textPrimary,
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(),
                  ),
                  const Spacer(),
                  ContinueAsGuestButton(onPressed: _continueAsGuest),
                ],
              ),
              const SizedBox(height: 40),
              const Text(
                'Enter your mobile number',
                style: TextStyle(
                  fontSize: 26,
                  fontWeight: FontWeight.w800,
                  color: OnboardingColors.textPrimary,
                  height: 1.2,
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                'Quick details, endless savings.',
                style: TextStyle(
                  fontSize: 15,
                  color: OnboardingColors.textSecondary,
                ),
              ),
              const SizedBox(height: 32),
              _PhoneInputField(
                controller: _controller,
                countryCode: _countryCode,
                onChanged: (_) => setState(() {}),
                onCountryTap: () => _showCountryPicker(context),
              ),
              const Spacer(),
              OnboardingPrimaryButton(
                label: 'Continue',
                enabled: _isValid,
                isLoading: isSending,
                onPressed: _isValid && !isSending ? _onContinue : null,
              ),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }

  void _showCountryPicker(BuildContext context) {
    showModalBottomSheet<void>(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Text('🇮🇳', style: TextStyle(fontSize: 24)),
              title: const Text('India'),
              trailing: const Text('+91'),
              onTap: () {
                setState(() => _countryCode = '+91');
                Navigator.pop(ctx);
              },
            ),
            ListTile(
              leading: const Text('🇺🇸', style: TextStyle(fontSize: 24)),
              title: const Text('United States'),
              trailing: const Text('+1'),
              onTap: () {
                setState(() => _countryCode = '+1');
                Navigator.pop(ctx);
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _PhoneInputField extends StatelessWidget {
  const _PhoneInputField({
    required this.controller,
    required this.countryCode,
    required this.onChanged,
    required this.onCountryTap,
  });

  final TextEditingController controller;
  final String countryCode;
  final ValueChanged<String> onChanged;
  final VoidCallback onCountryTap;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Padding(
          padding: EdgeInsets.only(left: 4, bottom: 6),
          child: Text(
            'Enter Mobile',
            style: TextStyle(
              color: OnboardingColors.primary,
              fontSize: 13,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
        Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: OnboardingColors.primary, width: 1.5),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
          child: Row(
            children: [
              InkWell(
                onTap: onCountryTap,
                borderRadius: BorderRadius.circular(6),
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        countryCode == '+91' ? '🇮🇳' : '🇺🇸',
                        style: const TextStyle(fontSize: 20),
                      ),
                      const SizedBox(width: 6),
                      Text(
                        countryCode,
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                          color: OnboardingColors.textPrimary,
                        ),
                      ),
                      const Icon(
                        Icons.keyboard_arrow_down,
                        size: 20,
                        color: OnboardingColors.textSecondary,
                      ),
                      const SizedBox(width: 12),
                      Container(
                        width: 1,
                        height: 24,
                        color: OnboardingColors.border,
                      ),
                      const SizedBox(width: 12),
                    ],
                  ),
                ),
              ),
              Expanded(
                child: TextField(
                  controller: controller,
                  keyboardType: TextInputType.phone,
                  inputFormatters: [
                    FilteringTextInputFormatter.digitsOnly,
                    LengthLimitingTextInputFormatter(10),
                  ],
                  onChanged: onChanged,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w500,
                  ),
                  decoration: const InputDecoration(
                    border: InputBorder.none,
                    hintText: '',
                    isDense: true,
                    contentPadding: EdgeInsets.symmetric(vertical: 14),
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}