from __future__ import annotations

import hashlib
import secrets
import time
from dataclasses import dataclass
from typing import Any, Literal


KemMode = Literal["classical", "pqc_stub", "hybrid"]
SigMode = Literal["classical", "pqc_stub", "hybrid"]


@dataclass(frozen=True)
class KemResult:
    mode: KemMode
    ok: bool
    details: dict[str, Any]


@dataclass(frozen=True)
class SignatureResult:
    mode: SigMode
    ok: bool
    details: dict[str, Any]


def _sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _kdf(label: str, *parts: bytes, out_len: int = 32) -> bytes:
    """
    Minimal demo KDF: SHA-256 over a labeled transcript.
    Not intended as a production KDF—used to keep the demo dependency-light.
    """
    h = hashlib.sha256()
    h.update(label.encode("utf-8"))
    for p in parts:
        h.update(b"\x00")
        h.update(p)
    digest = h.digest()
    if out_len <= len(digest):
        return digest[:out_len]
    # Expand deterministically if caller requests longer output.
    out = bytearray()
    counter = 0
    while len(out) < out_len:
        out.extend(_sha256(digest + counter.to_bytes(1, "big")))
        counter = (counter + 1) % 256
    return bytes(out[:out_len])


def _x25519_kem() -> tuple[bytes, bytes, dict[str, Any]]:
    """
    Classical KEM-like handshake via X25519 ECDH.
    Returns (client_ss, server_ss, details).
    """
    try:
        from cryptography.hazmat.primitives.asymmetric.x25519 import (
            X25519PrivateKey,
            X25519PublicKey,
        )
    except Exception as e:
        # Fallback: runnable demo without crypto libs (not cryptographically meaningful).
        c = secrets.token_bytes(32)
        s = c
        return c, s, {"warning": f"cryptography unavailable; using stub: {e}"}

    t0 = time.perf_counter()
    server_sk = X25519PrivateKey.generate()
    server_pk = server_sk.public_key()
    client_eph_sk = X25519PrivateKey.generate()
    client_eph_pk = client_eph_sk.public_key()

    ss_client = client_eph_sk.exchange(X25519PublicKey.from_public_bytes(server_pk.public_bytes_raw()))
    ss_server = server_sk.exchange(X25519PublicKey.from_public_bytes(client_eph_pk.public_bytes_raw()))
    t1 = time.perf_counter()

    # Derive fixed-length key material to resemble a KEM shared secret.
    c_ss = _kdf("x25519-demo", ss_client)
    s_ss = _kdf("x25519-demo", ss_server)
    return c_ss, s_ss, {"elapsed_ms": (t1 - t0) * 1000.0}


def _pqc_stub_kem() -> tuple[bytes, bytes, dict[str, Any]]:
    """
    Placeholder for ML-KEM (Kyber) style KEM.
    For now, it simulates encaps/decaps using random bytes and a transcript-bound KDF.
    """
    t0 = time.perf_counter()
    # In a real KEM: server has (pk, sk); client encapsulates to pk → (ct, ss_c); server decaps(ct) → ss_s.
    pk = secrets.token_bytes(32)
    ct = secrets.token_bytes(32)
    ss_c = _kdf("pqc-stub", pk, ct)
    ss_s = _kdf("pqc-stub", pk, ct)
    t1 = time.perf_counter()
    return ss_c, ss_s, {"elapsed_ms": (t1 - t0) * 1000.0, "note": "stub KEM (replace with ML-KEM library)"}


def kem_demo(mode: KemMode = "hybrid") -> KemResult:
    """
    Run a KEM/handshake demo suitable for a UI.

    - classical: X25519-based shared secret (via cryptography)
    - pqc_stub: placeholder KEM until a PQC library is added
    - hybrid: combine both secrets into final key material
    """
    details: dict[str, Any] = {}

    if mode == "classical":
        c_ss, s_ss, d = _x25519_kem()
        details["classical"] = d
        ok = secrets.compare_digest(c_ss, s_ss)
        return KemResult(mode=mode, ok=ok, details={"shared_secret_hex": c_ss.hex(), **details})

    if mode == "pqc_stub":
        c_ss, s_ss, d = _pqc_stub_kem()
        details["pqc"] = d
        ok = secrets.compare_digest(c_ss, s_ss)
        return KemResult(mode=mode, ok=ok, details={"shared_secret_hex": c_ss.hex(), **details})

    if mode == "hybrid":
        c1, s1, d1 = _x25519_kem()
        c2, s2, d2 = _pqc_stub_kem()
        ok = secrets.compare_digest(c1, s1) and secrets.compare_digest(c2, s2)
        if not ok:
            return KemResult(mode=mode, ok=False, details={"classical": d1, "pqc": d2})
        final_c = _kdf("hybrid-kem", c1, c2)
        final_s = _kdf("hybrid-kem", s1, s2)
        ok2 = secrets.compare_digest(final_c, final_s)
        return KemResult(
            mode=mode,
            ok=ok2,
            details={
                "hybrid_key_hex": final_c.hex(),
                "classical": d1,
                "pqc": d2,
                "note": "Hybrid key = KDF(classical_ss || pqc_ss)",
            },
        )

    raise ValueError(f"Unsupported mode: {mode}")


def _ed25519_sign_verify(message: bytes) -> tuple[bool, dict[str, Any]]:
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (
            Ed25519PrivateKey,
            Ed25519PublicKey,
        )
    except Exception as e:
        # Runnable fallback (not cryptographically meaningful).
        sig = _sha256(message)
        ok = secrets.compare_digest(sig, _sha256(message))
        return ok, {"warning": f"cryptography unavailable; using stub: {e}"}

    t0 = time.perf_counter()
    sk = Ed25519PrivateKey.generate()
    pk = sk.public_key()
    sig = sk.sign(message)
    ok = True
    try:
        Ed25519PublicKey.from_public_bytes(pk.public_bytes_raw()).verify(sig, message)
    except Exception:
        ok = False
    t1 = time.perf_counter()
    return ok, {"elapsed_ms": (t1 - t0) * 1000.0, "signature_bytes": len(sig)}


def _pqc_stub_signature(message: bytes) -> tuple[bool, dict[str, Any]]:
    """
    Placeholder for ML-DSA (Dilithium) style signatures.
    """
    t0 = time.perf_counter()
    # Simulate keypair + signature
    pk = secrets.token_bytes(32)
    sig = _kdf("pqc-sig-stub", pk, message, out_len=64)
    ok = secrets.compare_digest(sig, _kdf("pqc-sig-stub", pk, message, out_len=64))
    t1 = time.perf_counter()
    return ok, {"elapsed_ms": (t1 - t0) * 1000.0, "signature_bytes": len(sig), "note": "stub signature"}


def signature_demo(mode: SigMode = "hybrid", message: str = "hello, pqc") -> SignatureResult:
    """
    Signature demo:
    - classical: Ed25519 sign/verify
    - pqc_stub: placeholder PQ signature
    - hybrid: require both to verify
    """
    msg = message.encode("utf-8")

    if mode == "classical":
        ok, d = _ed25519_sign_verify(msg)
        return SignatureResult(mode=mode, ok=ok, details={"classical": d})

    if mode == "pqc_stub":
        ok, d = _pqc_stub_signature(msg)
        return SignatureResult(mode=mode, ok=ok, details={"pqc": d})

    if mode == "hybrid":
        ok1, d1 = _ed25519_sign_verify(msg)
        ok2, d2 = _pqc_stub_signature(msg)
        return SignatureResult(mode=mode, ok=(ok1 and ok2), details={"classical": d1, "pqc": d2})

    raise ValueError(f"Unsupported mode: {mode}")

