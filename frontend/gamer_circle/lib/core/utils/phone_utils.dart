/// Normalizes user-entered phone digits to E.164 for the Paythan backend.
String normalizePhoneNumber(String raw) {
  final trimmed = raw.trim();
  if (trimmed.startsWith('+')) {
    return '+${trimmed.substring(1).replaceAll(RegExp(r'\D'), '')}';
  }

  final digits = trimmed.replaceAll(RegExp(r'\D'), '');
  if (digits.isEmpty) return trimmed;

  // Default India country code for local dev (10-digit numbers).
  if (digits.length == 10) {
    return '+91$digits';
  }

  return '+$digits';
}