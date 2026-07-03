"""Auth schema validation tests."""

import pytest
from pydantic import ValidationError

from app.domains.auth.schemas import (
    LoginRequest,
    LoginRequestOtpRequest,
    LoginVerifyOtpRequest,
    SignupRequestOTPRequest,
    SignupVerifyOTPRequest,
)


def test_signup_request_otp_valid() -> None:
    req = SignupRequestOTPRequest(
        name="John Doe",
        username="johndoe",
        email="john@example.com",
        phone_number="+919876543210",
    )
    assert req.name == "John Doe"
    assert req.username == "johndoe"


def test_signup_request_otp_invalid_phone() -> None:
    with pytest.raises(ValidationError):
        SignupRequestOTPRequest(
            name="John",
            username="john",
            email="john@example.com",
            phone_number="abc",
        )


def test_signup_verify_weak_password() -> None:
    with pytest.raises(ValidationError):
        SignupVerifyOTPRequest(
            phone_number="+919876543210",
            otp="123456",
            password="weak",
        )


def test_signup_verify_password_with_special_chars() -> None:
    req = SignupVerifyOTPRequest(
        phone_number="+919876543210",
        otp="123456",
        password="New@123",
    )
    assert req.password == "New@123"


def test_signup_verify_strong_password() -> None:
    req = SignupVerifyOTPRequest(
        phone_number="+919876543210",
        otp="123456",
        password="SecurePass1",
    )
    assert req.otp == "123456"


def test_login_valid() -> None:
    req = LoginRequest(username="johndoe", password="SecurePass1")
    assert req.username == "johndoe"


def test_login_request_otp_valid() -> None:
    req = LoginRequestOtpRequest(phone_number="+919876543210")
    assert req.phone_number == "+919876543210"


def test_login_verify_otp_valid() -> None:
    req = LoginVerifyOtpRequest(phone_number="+919876543210", otp="123456")
    assert req.otp == "123456"