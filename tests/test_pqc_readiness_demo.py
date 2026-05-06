from __future__ import annotations

import re

import pytest

pytest.importorskip("cryptography")

from pqc_readiness.demo import kem_demo, signature_demo


def test_kem_demo_classical_ok() -> None:
    res = kem_demo(mode="classical")
    assert res.ok is True
    assert "shared_secret_hex" in res.details
    assert re.fullmatch(r"[0-9a-f]{64}", res.details["shared_secret_hex"]) is not None


def test_kem_demo_pqc_stub_ok() -> None:
    res = kem_demo(mode="pqc_stub")
    assert res.ok is True
    assert "shared_secret_hex" in res.details


def test_kem_demo_hybrid_ok() -> None:
    res = kem_demo(mode="hybrid")
    assert res.ok is True
    assert "hybrid_key_hex" in res.details
    assert re.fullmatch(r"[0-9a-f]{64}", res.details["hybrid_key_hex"]) is not None


def test_signature_demo_classical_ok() -> None:
    res = signature_demo(mode="classical", message="msg")
    assert res.ok is True
    assert "classical" in res.details


def test_signature_demo_hybrid_ok() -> None:
    res = signature_demo(mode="hybrid", message="msg")
    assert res.ok is True
    assert "classical" in res.details and "pqc" in res.details

