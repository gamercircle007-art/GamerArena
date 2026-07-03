/// Shared password rules — must stay aligned with backend auth schemas.
class PasswordUtils {
  PasswordUtils._();

  static const int minLength = 6;

  static final RegExp _strengthPattern = RegExp(
    r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$',
  );

  static String? validate(String? value) {
    if (value == null || value.isEmpty) {
      return 'Please enter a password';
    }
    if (value.length < minLength) {
      return 'Password must be at least $minLength characters';
    }
    if (!_strengthPattern.hasMatch(value)) {
      return 'Include uppercase, lowercase, and a number';
    }
    return null;
  }
}