"""Tests for OYO-style gaming booking reference generation."""

import re

import pytest

from app.domains.gaming_booking.booking_ref import _random_segment


_REF_PATTERN = re.compile(r"^[A-Z][0-9][A-Z][0-9]{5}$")


def test_random_segment_format() -> None:
    for _ in range(100):
        ref = _random_segment()
        assert _REF_PATTERN.match(ref), ref


def test_random_segment_uniqueness_sample() -> None:
    refs = {_random_segment() for _ in range(200)}
    assert len(refs) >= 190