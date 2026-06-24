sealed class SignUpState {
  const SignUpState();
}

final class SignUpInitial extends SignUpState {
  const SignUpInitial();
}

final class SignUpLoading extends SignUpState {
  const SignUpLoading();
}

/// OTP has been sent — phone + password stored for verify step.
final class OtpSent extends SignUpState {
  final String phone;
  final String password;
  const OtpSent(this.phone, this.password);
}

final class OtpVerifying extends SignUpState {
  const OtpVerifying();
}

final class SignUpError extends SignUpState {
  final String message;
  const SignUpError(this.message);
}