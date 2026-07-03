sealed class LoginPasswordState {
  const LoginPasswordState();
}

final class LoginPasswordInitial extends LoginPasswordState {
  const LoginPasswordInitial();
}

final class LoginPasswordLoading extends LoginPasswordState {
  const LoginPasswordLoading();
}

final class LoginPasswordError extends LoginPasswordState {
  final String message;
  const LoginPasswordError(this.message);
}