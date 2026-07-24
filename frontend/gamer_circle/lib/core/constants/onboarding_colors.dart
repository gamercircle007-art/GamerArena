import 'package:flutter/material.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';

/// Backward-compatible aliases — all values come from [AppColors].
class OnboardingColors {
  OnboardingColors._();

  static const Color primary = AppColors.primary;
  static const Color primaryDark = AppColors.primaryDark;
  static const Color textPrimary = AppColors.textPrimaryLight;
  static const Color textSecondary = AppColors.textSecondaryLight;
  static const Color textMuted = AppColors.textSecondaryLight;
  static const Color border = AppColors.borderLight;
  static const Color disabledButton = AppColors.disabled;
  static const Color guestPillBg = AppColors.guestPillBg;
  static const Color permissionIconBg = AppColors.primaryLight;
  static const Color homeBlue = AppColors.secondary;
  static const Color payBillRed = AppColors.error;
  static const Color walletGold = AppColors.warning;

  static const welcomeGradient = AppColors.welcomeGradient;
}