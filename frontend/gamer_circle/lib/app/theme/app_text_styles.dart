import 'package:flutter/material.dart';
import 'app_colors.dart';

/// Single source of truth for every text style in the app.
/// Never write `TextStyle(fontSize: 16, ...)` inline in a widget —
/// use AppTextStyles.xyz instead. Change font/weight/size here, it updates everywhere.
class AppTextStyles {
  AppTextStyles._();

  static const String fontFamily = 'Inter'; // swap freely — one line change

  // ---- Display / Headlines ----
  static const TextStyle displayLarge = TextStyle(
    fontFamily: fontFamily,
    fontSize: 32,
    fontWeight: FontWeight.w700,
    height: 1.2,
  );

  static const TextStyle headlineMedium = TextStyle(
    fontFamily: fontFamily,
    fontSize: 24,
    fontWeight: FontWeight.w700,
    height: 1.25,
  );

  static const TextStyle headlineSmall = TextStyle(
    fontFamily: fontFamily,
    fontSize: 20,
    fontWeight: FontWeight.w600,
    height: 1.3,
  );

  // ---- Body ----
  static const TextStyle bodyLarge = TextStyle(
    fontFamily: fontFamily,
    fontSize: 16,
    fontWeight: FontWeight.w400,
    height: 1.5,
  );

  static const TextStyle bodyMedium = TextStyle(
    fontFamily: fontFamily,
    fontSize: 14,
    fontWeight: FontWeight.w400,
    height: 1.5,
  );

  static const TextStyle bodySmall = TextStyle(
    fontFamily: fontFamily,
    fontSize: 12,
    fontWeight: FontWeight.w400,
    height: 1.4,
  );

  // ---- Labels / Buttons ----
  static const TextStyle labelLarge = TextStyle(
    fontFamily: fontFamily,
    fontSize: 16,
    fontWeight: FontWeight.w600,
    height: 1.2,
  );

  static const TextStyle labelSmall = TextStyle(
    fontFamily: fontFamily,
    fontSize: 12,
    fontWeight: FontWeight.w500,
    height: 1.2,
    letterSpacing: 0.4,
  );

  // ---- Color-applied convenience variants (light mode) ----
  static TextStyle bodyMediumMuted = bodyMedium.copyWith(
    color: AppColors.textSecondaryLight,
  );

  static TextStyle errorText = bodySmall.copyWith(color: AppColors.error);
}
