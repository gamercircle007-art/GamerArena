import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:gamer_circle/app/config/app_config.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/constants/app_constants.dart';
import 'package:gamer_circle/core/services/api_status_service.dart';
import 'package:gamer_circle/core/utils/login_identifier_utils.dart';
import 'package:gamer_circle/features/auth/presentation/providers/login_otp_providers.dart';
import 'package:gamer_circle/features/auth/presentation/providers/login_otp_state.dart';
import 'package:gamer_circle/features/auth/presentation/providers/login_password_providers.dart';
import 'package:gamer_circle/features/auth/presentation/providers/login_password_state.dart';
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
  final _identifierController = TextEditingController();
  final _passwordController = TextEditingController();
  String _otp = '';
  int _secondsLeft = 0;
  Timer? _timer;
  bool _obscurePassword = true;
  ApiStatusResult? _apiStatus;
  bool _checkingApi = false;

  @override
  void initState() {
    super.initState();
    _probeApi();
  }

  Future<void> _probeApi() async {
    setState(() => _checkingApi = true);
    final result = await ApiStatusService().check();
    if (!mounted) return;
    setState(() {
      _apiStatus = result;
      _checkingApi = false;
    });
  }

  @override
  void dispose() {
    _identifierController.dispose();
    _passwordController.dispose();
    _timer?.cancel();
    super.dispose();
  }

  bool get _isPhoneLogin {
    final value = _identifierController.text.trim();
    return value.isNotEmpty && isPhoneIdentifier(value);
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
    final phone = _activePhone ?? _identifierController.text.trim();
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

    ref.listen<LoginPasswordState>(loginPasswordNotifierProvider, (_, next) {
      if (next is LoginPasswordError) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(next.message),
            backgroundColor: Colors.red.shade700,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    });

    final loginOtpState = ref.watch(loginOtpNotifierProvider);
    final loginPasswordState = ref.watch(loginPasswordNotifierProvider);
    final showOtpStep = _showOtpStep(loginOtpState);
    final isSendingOtp = loginOtpState is LoginOtpSending;
    final isVerifyingOtp = loginOtpState is LoginOtpVerifying;
    final isPasswordLoading = loginPasswordState is LoginPasswordLoading;

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
                        color: AppColors.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 8),
                    if (showOtpStep)
                      RichText(
                        text: TextSpan(
                          text: 'Code sent to ',
                          style: const TextStyle(
                            fontSize: 14,
                            color: AppColors.textSecondary,
                          ),
                          children: [
                            TextSpan(
                              text: _maskedPhone,
                              style: const TextStyle(
                                fontWeight: FontWeight.bold,
                                color: AppColors.textPrimary,
                              ),
                            ),
                          ],
                        ),
                      )
                    else
                      const Text(
                        'Sign in with phone number or username',
                        style: TextStyle(
                          fontSize: 14,
                          color: AppColors.textSecondary,
                        ),
                      ),
                    const SizedBox(height: 16),
                    _buildApiStatusBanner(),
                    const SizedBox(height: 12),
                    if (!showOtpStep) ...[
                      _buildIdentifierField(
                        enabled: !isSendingOtp && !isPasswordLoading,
                      ),
                      const SizedBox(height: 16),
                      if (_isPhoneLogin) ...[
                        _GradientButton(
                          label: 'Send OTP',
                          isLoading: isSendingOtp,
                          onPressed: isSendingOtp ? null : _onSendOtp,
                        ),
                      ] else ...[
                        _buildPasswordField(
                          enabled: !isPasswordLoading,
                        ),
                        const SizedBox(height: 28),
                        _GradientButton(
                          label: 'Login',
                          isLoading: isPasswordLoading,
                          onPressed: isPasswordLoading ? null : _onPasswordLogin,
                        ),
                      ],
                    ] else ...[
                      OtpInputWidget(
                        onChanged: (otp) => setState(() => _otp = otp),
                        onCompleted: (otp) => setState(() => _otp = otp),
                      ),
                      const SizedBox(height: 28),
                      _GradientButton(
                        label: 'Verify & Login',
                        isLoading: isVerifyingOtp,
                        onPressed: (_otp.length == 6 && !isVerifyingOtp)
                            ? _onVerifyOtp
                            : null,
                      ),
                      const SizedBox(height: 16),
                      _buildOtpActions(),
                      if (!kReleaseMode && !AppConfig.instance.isProd) ...[
                        const SizedBox(height: 16),
                        Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: AppColors.primaryLight,
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(
                              color: AppColors.primary.withOpacity(0.3),
                            ),
                          ),
                          child: Row(
                            children: [
                              const Icon(
                                Icons.info_outline,
                                color: AppColors.primary,
                                size: 18,
                              ),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  'Dev mode — OTP is: ${AppConstants.devOtpBypass}',
                                  style: const TextStyle(
                                    color: AppColors.primary,
                                    fontSize: 13,
                                    fontWeight: FontWeight.w500,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ],
                    const SizedBox(height: 20),
                    Center(
                      child: TextButton(
                        onPressed: () => context.push('/login/signup'),
                        child: RichText(
                          text: const TextSpan(
                            text: 'New user? ',
                            style: TextStyle(
                              color: AppColors.textSecondary,
                              fontSize: 14,
                            ),
                            children: [
                              TextSpan(
                                text: 'Sign Up',
                                style: TextStyle(
                                  color: AppColors.secondary,
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

  Widget _buildIdentifierField({required bool enabled}) {
    return TextFormField(
      controller: _identifierController,
      enabled: enabled,
      keyboardType: TextInputType.text,
      textInputAction: TextInputAction.next,
      style: const TextStyle(
        color: AppColors.textPrimary,
        fontSize: 16,
        fontWeight: FontWeight.w500,
      ),
      cursorColor: AppColors.primary,
      onChanged: (_) => setState(() {}),
      onFieldSubmitted: (_) {
        if (_isPhoneLogin) {
          _onSendOtp();
        } else {
          _onPasswordLogin();
        }
      },
      decoration: InputDecoration(
        hintText: 'Phone Number or Username',
        hintStyle: const TextStyle(color: AppColors.textSecondary),
        prefixIcon: Icon(
          _isPhoneLogin ? Icons.phone_outlined : Icons.alternate_email,
          color: AppColors.primary,
        ),
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
          borderSide: const BorderSide(color: AppColors.primary, width: 2),
        ),
        filled: true,
        fillColor: Colors.white,
      ),
      validator: validateLoginIdentifier,
    );
  }

  Widget _buildPasswordField({required bool enabled}) {
    return TextFormField(
      controller: _passwordController,
      enabled: enabled,
      obscureText: _obscurePassword,
      textInputAction: TextInputAction.done,
      style: const TextStyle(
        color: AppColors.textPrimary,
        fontSize: 16,
        fontWeight: FontWeight.w500,
      ),
      cursorColor: AppColors.primary,
      onFieldSubmitted: (_) => _onPasswordLogin(),
      decoration: InputDecoration(
        hintText: 'Password',
        hintStyle: const TextStyle(color: AppColors.textSecondary),
        prefixIcon: const Icon(Icons.lock_outline, color: AppColors.primary),
        suffixIcon: IconButton(
          icon: Icon(
            _obscurePassword
                ? Icons.visibility_off_outlined
                : Icons.visibility_outlined,
            color: AppColors.textSecondary,
          ),
          onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
        ),
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
          borderSide: const BorderSide(color: AppColors.primary, width: 2),
        ),
        filled: true,
        fillColor: Colors.white,
      ),
      validator: (value) {
        if (value == null || value.isEmpty) {
          return 'Please enter your password';
        }
        return null;
      },
    );
  }

  Widget _buildApiStatusBanner() {
    if (_checkingApi) {
      return Container(
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(
          color: Colors.grey.shade100,
          borderRadius: BorderRadius.circular(8),
        ),
        child: const Row(
          children: [
            SizedBox(
              width: 14,
              height: 14,
              child: CircularProgressIndicator(strokeWidth: 2),
            ),
            SizedBox(width: 10),
            Expanded(
              child: Text(
                'Checking API…',
                style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
              ),
            ),
          ],
        ),
      );
    }
    final status = _apiStatus;
    if (status == null) return const SizedBox.shrink();
    final ok = status.ok;
    return Material(
      color: ok ? const Color(0xFFE8F5E9) : const Color(0xFFFFEBEE),
      borderRadius: BorderRadius.circular(8),
      child: InkWell(
        onTap: _probeApi,
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: const EdgeInsets.all(10),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(
                ok ? Icons.cloud_done : Icons.cloud_off,
                size: 18,
                color: ok ? Colors.green.shade800 : Colors.red.shade800,
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      status.display,
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: ok ? Colors.green.shade900 : Colors.red.shade900,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      AppConstants.baseUrl,
                      style: TextStyle(
                        fontSize: 10,
                        color: Colors.grey.shade700,
                      ),
                    ),
                    if (!ok)
                      Text(
                        'Tap to recheck · password login if OTP fails',
                        style: TextStyle(
                          fontSize: 10,
                          color: Colors.red.shade700,
                        ),
                      ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildOtpActions() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        TextButton(
          onPressed: _onChangeIdentifier,
          child: const Text(
            'Change number',
            style: TextStyle(
              color: AppColors.secondary,
              fontSize: 13,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
        _secondsLeft > 0
            ? Text(
                'Resend in ${_secondsLeft}s',
                style: const TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: 13,
                ),
              )
            : TextButton(
                onPressed: _onResendOtp,
                child: const Text(
                  'Resend OTP',
                  style: TextStyle(
                    color: AppColors.secondary,
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
          _identifierController.text.trim(),
        );
  }

  void _onPasswordLogin() {
    if (!_formKey.currentState!.validate()) return;
    ref.read(loginPasswordNotifierProvider.notifier).login(
          username: _identifierController.text.trim(),
          password: _passwordController.text,
        );
  }

  void _onVerifyOtp() {
    if (_otp.length != 6) return;
    ref.read(loginOtpNotifierProvider.notifier).verifyOtp(_otp);
  }

  void _onResendOtp() {
    final phone = _activePhone ?? _identifierController.text.trim();
    if (phone.isEmpty) return;
    ref.read(loginOtpNotifierProvider.notifier).requestOtp(phone);
  }

  void _onChangeIdentifier() {
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
                colors: [AppColors.primary, AppColors.secondary],
              ),
        boxShadow: onPressed == null
            ? null
            : [
                BoxShadow(
                  color: AppColors.primary.withOpacity(0.4),
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