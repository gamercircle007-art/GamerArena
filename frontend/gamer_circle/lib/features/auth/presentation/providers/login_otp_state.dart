sealed class LoginOtpState {
  const LoginOtpState();
}

final class LoginOtpInitial extends LoginOtpState {
  const LoginOtpInitial();
}

final class LoginOtpSending extends LoginOtpState {
  const LoginOtpSending();
}

final class LoginOtpSent extends LoginOtpState {
  final String phone;
  const LoginOtpSent(this.phone);
}

final class LoginOtpVerifying extends LoginOtpState {
  final String phone;
  const LoginOtpVerifying(this.phone);
}

final class LoginOtpError extends LoginOtpState {
  final String message;
  final String? phone;
  const LoginOtpError(this.message, {this.phone});
}