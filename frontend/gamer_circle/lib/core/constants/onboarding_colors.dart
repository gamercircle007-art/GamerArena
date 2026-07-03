import 'package:flutter/material.dart';

/// Brand palette matching the reference onboarding / home designs.
class OnboardingColors {
  OnboardingColors._();

  static const Color primary = Color(0xFFFF5500);
  static const Color primaryDark = Color(0xFFE64A00);
  static const Color textPrimary = Color(0xFF1A1A1A);
  static const Color textSecondary = Color(0xFF888888);
  static const Color textMuted = Color(0xFFAAAAAA);
  static const Color border = Color(0xFFE8E8E8);
  static const Color disabledButton = Color(0xFFBDBDBD);
  static const Color guestPillBg = Color(0xFFF0F0F0);
  static const Color permissionIconBg = Color(0xFFFFF0EB);
  static const Color homeBlue = Color(0xFF1B6EF3);
  static const Color payBillRed = Color(0xFFE31E24);
  static const Color walletGold = Color(0xFFFFB800);

  static const LinearGradient welcomeGradient = LinearGradient(
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
    colors: [Color(0xFFFFF8F5), Color(0xFFFFFFFF)],
  );
}