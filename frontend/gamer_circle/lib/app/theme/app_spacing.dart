/// Single source of truth for spacing, radius, and sizing in the app.
/// Never write `SizedBox(height: 16)` or `EdgeInsets.all(12)` with a raw
/// number inline — use AppSpacing.xyz instead. Change the scale here,
/// every screen's spacing updates consistently.
class AppSpacing {
  AppSpacing._();

  // ---- Base spacing scale ----
  static const double xs = 4;
  static const double sm = 8;
  static const double md = 16;
  static const double lg = 24;
  static const double xl = 32;
  static const double xxl = 48;

  // ---- Border radius scale ----
  static const double radiusSm = 6;
  static const double radiusMd = 12;
  static const double radiusLg = 20;
  static const double radiusFull = 999;

  // ---- Common component sizing ----
  static const double buttonHeight = 48;
  static const double inputHeight = 52;
  static const double iconSm = 16;
  static const double iconMd = 24;
  static const double iconLg = 32;
  static const double avatarSm = 32;
  static const double avatarMd = 48;
  static const double avatarLg = 72;

  // ---- Screen-level padding ----
  static const double screenPaddingH = md;
  static const double screenPaddingV = lg;
}
