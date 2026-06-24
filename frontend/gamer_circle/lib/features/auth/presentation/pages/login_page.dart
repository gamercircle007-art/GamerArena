import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/constants/app_constants.dart';
import 'package:gamer_circle/features/auth/presentation/providers/login_otp_providers.dart';
import 'package:gamer_circle/features/auth/presentation/providers/login_otp_state.dart';
import 'package:gamer_circle/features/auth/presentation/widgets/gradient_header_widget.dart';
import 'package:gamer_circle/features/auth/presentation/widgets/otp_input_widget.dart';
import 'package:gamer_circle/features/auth/presentation/widgets/social_login_row_widget.dart';

class LoginPage extends ConsumerStatefulWidget {
  const LoginPage({super.key});

  @override
  ConsumerState<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends ConsumerState<LoginPage> {
  final _formKey = GlobalKey<FormState>();
  final _phoneController = TextEditingController();
  String _otp = '';
  int _secondsLeft = 0;
  Timer? _timer;

  @override
  void dispose() {
    _phoneController.dispose();
    _timer?.cancel();
    super.dispose();
  }

  bool _showOtpStep(LoginOtpState state) =>
      state is LoginOtpSent ||
      state is LoginOtpVerifying ||
      (state is LoginOtpError && state.phone != null);

  String? get _activePhone {
    final state = ref.read(loginOtpNotifierProvider);
    return switch (state) {
      LoginOtpSent(:final phone) => phone,
      LoginOtpVerifying(:final phone) => phone,
      LoginOtpError(:final phone?) => phone,
      _ => null,
    };
  }

  String get _maskedPhone {
    final phone = _activePhone ?? _phoneController.text.trim();
    if (phone.length < 4) return phone;
    return '${'*' * (phone.length - 4)}${phone.substring(phone.length - 4)}';
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

  @override
  Widget build(BuildContext context) {
    ref.listen<LoginOtpState>(loginOtpNotifierProvider, (prev, next) {
      if (next is LoginOtpError) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(next.message),
            backgroundColor: Colors.red.shade700,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
      if (next is LoginOtpSent) {
        _startResendTimer();
      }
    });

    final loginState = ref.watch(loginOtpNotifierProvider);
    final showOtpStep = _showOtpStep(loginState);
    final isSending = loginState is LoginOtpSending;
    final isVerifying = loginState is LoginOtpVerifying;

    return Scaffold(
      backgroundColor: Colors.white,
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const GradientHeaderWidget(),
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 32, 24, 24),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text(
                      showOtpStep ? 'Enter OTP' : 'Welcome back !',
                      style: const TextStyle(
                        fontSize: 26,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF1A1A2E),
                      ),
                    ),
                    const SizedBox(height: 8),
                    if (showOtpStep)
                      RichText(
                        text: TextSpan(
                          text: 'Code sent to ',
                          style: const TextStyle(
                            fontSize: 14,
                            color: Color(0xFF888888),
                          ),
                          children: [
                            TextSpan(
                              text: _maskedPhone,
                              style: const TextStyle(
                                fontWeight: FontWeight.bold,
                                color: Color(0xFF1A1A2E),
                              ),
                            ),
                          ],
                        ),
                      )
                    else
                      const Text(
                        'Sign in with your phone number',
                        style: TextStyle(
                          fontSize: 14,
                          color: Color(0xFF888888),
                        ),
                      ),
                    const SizedBox(height: 28),
                    if (!showOtpStep) ...[
                      _buildPhoneField(enabled: !isSending),
                      const SizedBox(height: 28),
                      _GradientButton(
                        label: 'Send OTP',
                        isLoading: isSending,
                        onPressed: isSending ? null : _onSendOtp,
                      ),
                    ] else ...[
                      OtpInputWidget(
                        onChanged: (otp) => setState(() => _otp = otp),
                        onCompleted: (otp) => setState(() => _otp = otp),
                      ),
                      const SizedBox(height: 28),
                      _GradientButton(
                        label: 'Verify & Login',
                        isLoading: isVerifying,
                        onPressed: (_otp.length == 6 && !isVerifying)
                            ? _onVerifyOtp
                            : null,
                      ),
                      const SizedBox(height: 16),
                      _buildOtpActions(),
                      const SizedBox(height: 16),
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: const Color(0xFFF3E8FF),
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(
                            color: const Color(0xFF7B2FF7).withOpacity(0.3),
                          ),
                        ),
                        child: Row(
                          children: [
                            const Icon(
                              Icons.info_outline,
                              color: Color(0xFF7B2FF7),
                              size: 18,
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                'Dev mode — OTP is: ${AppConstants.devOtpBypass}',
                                style: const TextStyle(
                                  color: Color(0xFF7B2FF7),
                                  fontSize: 13,
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                    const SizedBox(height: 20),
                    Center(
                      child: TextButton(
                        onPressed: () => context.push('/login/signup'),
                        child: RichText(
                          text: const TextSpan(
                            text: 'New user? ',
                            style: TextStyle(
                              color: Color(0xFF888888),
                              fontSize: 14,
                            ),
                            children: [
                              TextSpan(
                                text: 'Sign Up',
                                style: TextStyle(
                                  color: Color(0xFF3B82F6),
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 32),
                    const SocialLoginRowWidget(),
                    const SizedBox(height: 16),
                    const Center(
                      child: Text(
                        'Sign in with another account',
                        style: TextStyle(
                          color: Color(0xFFAAAAAA),
                          fontSize: 12,
                        ),
                      ),
                    ),
                    const SizedBox(height: 24),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPhoneField({required bool enabled}) {
    return TextFormField(
      controller: _phoneController,
      enabled: enabled,
      keyboardType: TextInputType.phone,
      textInputAction: TextInputAction.done,
      inputFormatters: [FilteringTextInputFormatter.digitsOnly],
      onFieldSubmitted: (_) => _onSendOtp(),
      decoration: InputDecoration(
        hintText: 'Phone Number',
        prefixIcon: const Icon(Icons.phone_outlined, color: Color(0xFF7B2FF7)),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFFE0E0E0)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFFE0E0E0)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFF7B2FF7), width: 2),
        ),
        filled: true,
        fillColor: const Color(0xFFF9F9F9),
      ),
      validator: (value) {
        if (value == null || value.trim().isEmpty) {
          return 'Please enter your phone number';
        }
        if (value.trim().length < 10) {
          return 'Enter a valid phone number';
        }
        return null;
      },
    );
  }

  Widget _buildOtpActions() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        TextButton(
          onPressed: _onChangePhone,
          child: const Text(
            'Change number',
            style: TextStyle(
              color: Color(0xFF3B82F6),
              fontSize: 13,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
        _secondsLeft > 0
            ? Text(
                'Resend in ${_secondsLeft}s',
                style: const TextStyle(
                  color: Color(0xFF888888),
                  fontSize: 13,
                ),
              )
            : TextButton(
                onPressed: _onResendOtp,
                child: const Text(
                  'Resend OTP',
                  style: TextStyle(
                    color: Color(0xFF3B82F6),
                    fontSize: 13,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
      ],
    );
  }

  void _onSendOtp() {
    if (!_formKey.currentState!.validate()) return;
    ref.read(loginOtpNotifierProvider.notifier).requestOtp(
          _phoneController.text.trim(),
        );
  }

  void _onVerifyOtp() {
    if (_otp.length != 6) return;
    ref.read(loginOtpNotifierProvider.notifier).verifyOtp(_otp);
  }

  void _onResendOtp() {
    final phone = _activePhone ?? _phoneController.text.trim();
    if (phone.isEmpty) return;
    ref.read(loginOtpNotifierProvider.notifier).requestOtp(phone);
  }

  void _onChangePhone() {
    _timer?.cancel();
    setState(() {
      _otp = '';
      _secondsLeft = 0;
    });
    ref.read(loginOtpNotifierProvider.notifier).reset();
  }
}

class _GradientButton extends StatelessWidget {
  final String label;
  final bool isLoading;
  final VoidCallback? onPressed;

  const _GradientButton({
    required this.label,
    required this.isLoading,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(30),
        gradient: onPressed == null
            ? const LinearGradient(
                colors: [Color(0xFFBBBBBB), Color(0xFFBBBBBB)],
              )
            : const LinearGradient(
                begin: Alignment.centerLeft,
                end: Alignment.centerRight,
                colors: [Color(0xFF7B2FF7), Color(0xFF3B82F6)],
              ),
        boxShadow: onPressed == null
            ? null
            : [
                BoxShadow(
                  color: const Color(0xFF7B2FF7).withOpacity(0.4),
                  blurRadius: 12,
                  offset: const Offset(0, 4),
                ),
              ],
      ),
      child: ElevatedButton(
        onPressed: onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.transparent,
          shadowColor: Colors.transparent,
          minimumSize: const Size(double.infinity, 52),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(30),
          ),
        ),
        child: isLoading
            ? const SizedBox(
                width: 22,
                height: 22,
                child: CircularProgressIndicator(
                  color: Colors.white,
                  strokeWidth: 2.5,
                ),
              )
            : Text(
                label,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 0.5,
                ),
              ),
      ),
    );
  }
}