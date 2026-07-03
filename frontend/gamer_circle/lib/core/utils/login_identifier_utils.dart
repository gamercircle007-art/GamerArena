final _usernamePattern = RegExp(r'^[a-zA-Z][a-zA-Z0-9_]{2,29}$');

bool isPhoneIdentifier(String value) {
  final trimmed = value.trim();
  if (trimmed.isEmpty) return false;

  if (trimmed.startsWith('+')) {
    final digits = trimmed.substring(1).replaceAll(RegExp(r'\D'), '');
    return digits.length >= 10;
  }

  final digits = trimmed.replaceAll(RegExp(r'\D'), '');
  return digits.length == trimmed.length && digits.length >= 10;
}

bool isValidUsername(String value) => _usernamePattern.hasMatch(value.trim());

String? validateLoginIdentifier(String? value) {
  if (value == null || value.trim().isEmpty) {
    return 'Enter your phone number or username';
  }

  final trimmed = value.trim();
  if (isPhoneIdentifier(trimmed)) {
    final digits = trimmed.replaceAll(RegExp(r'\D'), '');
    if (digits.length < 10) {
      return 'Enter a valid phone number';
    }
    return null;
  }

  if (!isValidUsername(trimmed)) {
    return 'Username must be 3-30 chars, start with a letter';
  }
  return null;
}

String? validateSignupUsername(String? value) {
  if (value == null || value.trim().isEmpty) {
    return 'Please choose a username';
  }
  if (!isValidUsername(value.trim())) {
    return '3-30 chars, start with a letter, letters/numbers/_ only';
  }
  return null;
}