import 'package:flutter/material.dart';

/// Single source of truth for every color used in the app.
/// Never hardcode a Color(0x...) or Colors.xyz directly in a screen/widget —
/// reference AppColors.xyz instead. Changing a value here updates the whole app.
class AppColors {
  AppColors._(); // prevent instantiation

  // ---- Brand ----
  static const Color primary = Color(0xFF4F46E5);
  static const Color primaryDark = Color(0xFF3730A3);
  static const Color primaryLight = Color(0xFFC7D2FE);

  static const Color secondary = Color(0xFF10B981);
  static const Color secondaryDark = Color(0xFF047857);
  static const Color secondaryLight = Color(0xFFA7F3D0);

  // ---- Neutrals (light mode) ----
  static const Color backgroundLight = Color(0xFFFAFAFA);
  static const Color surfaceLight = Color(0xFFFFFFFF);
  static const Color textPrimaryLight = Color(0xFF111827);
  static const Color textSecondaryLight = Color(0xFF6B7280);
  static const Color borderLight = Color(0xFFE5E7EB);

  // ---- Neutrals (dark mode) ----
  static const Color backgroundDark = Color(0xFF0F1115);
  static const Color surfaceDark = Color(0xFF1A1D23);
  static const Color textPrimaryDark = Color(0xFFF9FAFB);
  static const Color textSecondaryDark = Color(0xFF9CA3AF);
  static const Color borderDark = Color(0xFF2D313A);

  // ---- Semantic / feedback ----
  static const Color success = Color(0xFF22C55E);
  static const Color warning = Color(0xFFF59E0B);
  static const Color error = Color(0xFFEF4444);
  static const Color info = Color(0xFF3B82F6);

  // ---- Domain-specific (extend as needed) ----
  static const Color bookingConfirmed = success;
  static const Color bookingPending = warning;
  static const Color bookingCancelled = error;
  static const Color onlineStatus = success;
  static const Color offlineStatus = Color(0xFF9CA3AF);

  // ---- Legacy / convenience aliases (for gradual migration) ----
  static const Color primaryMuted = primaryLight;
  static const Color accent = primaryLight;
  static const Color background = backgroundLight;
  static const Color surface = surfaceLight;
  static const Color textPrimary = textPrimaryLight;
  static const Color textSecondary = textSecondaryLight;
  static const Color textMuted = textSecondaryLight;
  static const Color textOnPrimary = Colors.white;
  static const Color border = borderLight;
  static const Color divider = borderLight;
  static const Color disabled = Color(0xFFBDBDBD);
  static const Color guestPillBg = Color(0xFFFFF0E8);

  // ---- Gradients (kept for compatibility) ----
  static const LinearGradient brandGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [primary, secondary],
  );

  static const LinearGradient brandGradientVertical = LinearGradient(
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
    colors: [primary, primaryDark],
  );

  static const LinearGradient welcomeGradient = LinearGradient(
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
    colors: [Color(0xFFFAFAFA), surfaceLight],
  );

  static const LinearGradient storyRingGradient = LinearGradient(
    colors: [primary, secondary],
  );

  // ---- DM / Instagram-style dark messaging palette (pure black aesthetic) ----
  // Kept for the messaging redesign to match reference screenshots
  static const Color dmBackground = Color(0xFF000000);
  static const Color dmSurface = Color(0xFF121212);
  static const Color dmCard = Color(0xFF1C1C1E);
  static const Color dmDivider = Color(0xFF2C2C2E);
  static const Color dmTextPrimary = Color(0xFFFFFFFF);
  static const Color dmTextSecondary = Color(0xFF8E8E93);
  static const Color dmTextMuted = Color(0xFF636366);
  static const Color dmBlue = Color(0xFF0095F6);
  static const Color dmRed = Color(0xFFFF3B30);
  static const Color dmSearchBg = Color(0xFF1C1C1E);
  static const Color dmPillBg = Color(0xFF2C2C2E);
}