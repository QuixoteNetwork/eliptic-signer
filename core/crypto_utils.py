from __future__ import annotations

import base64
import hashlib
from pathlib import Path
from typing import Optional

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import (
    BestAvailableEncryption,
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)


class CryptoManager:
    @staticmethod
    def generate_private_key() -> Ed25519PrivateKey:
        return Ed25519PrivateKey.generate()

    @staticmethod
    def get_public_key(private_key: Ed25519PrivateKey) -> Ed25519PublicKey:
        return private_key.public_key()

    @staticmethod
    def private_key_to_pem(
        private_key: Ed25519PrivateKey,
        password: Optional[str] = None,
    ) -> bytes:
        if password:
            enc = BestAvailableEncryption(password.encode("utf-8"))
        else:
            enc = NoEncryption()

        return private_key.private_bytes(
            encoding=Encoding.PEM,
            format=PrivateFormat.PKCS8,
            encryption_algorithm=enc,
        )

    @staticmethod
    def public_key_to_pem(public_key: Ed25519PublicKey) -> bytes:
        return public_key.public_bytes(
            encoding=Encoding.PEM,
            format=PublicFormat.SubjectPublicKeyInfo,
        )

    @staticmethod
    def public_key_to_pem_text(public_key: Ed25519PublicKey) -> str:
        return CryptoManager.public_key_to_pem(public_key).decode("utf-8")

    @staticmethod
    def public_key_to_base64(public_key: Ed25519PublicKey) -> str:
        raw = public_key.public_bytes(
            encoding=Encoding.Raw,
            format=PublicFormat.Raw,
        )
        return base64.b64encode(raw).decode("ascii")

    @staticmethod
    def save_private_key(
        private_key: Ed25519PrivateKey,
        path: str | Path,
        password: Optional[str] = None,
    ) -> None:
        Path(path).write_bytes(
            CryptoManager.private_key_to_pem(private_key, password)
        )

    @staticmethod
    def save_public_key(public_key: Ed25519PublicKey, path: str | Path) -> None:
        Path(path).write_bytes(CryptoManager.public_key_to_pem(public_key))

    @staticmethod
    def load_private_key(
        path: str | Path,
        password: Optional[str] = None,
    ) -> Ed25519PrivateKey:
        data = Path(path).read_bytes()
        key = serialization.load_pem_private_key(
            data,
            password=password.encode("utf-8") if password else None,
        )
        if not isinstance(key, Ed25519PrivateKey):
            raise TypeError("The loaded private key is not Ed25519")
        return key

    @staticmethod
    def load_public_key(path: str | Path) -> Ed25519PublicKey:
        key = serialization.load_pem_public_key(Path(path).read_bytes())
        if not isinstance(key, Ed25519PublicKey):
            raise TypeError("The loaded public key is not Ed25519")
        return key

    @staticmethod
    def load_public_key_from_pem_text(pem_text: str) -> Ed25519PublicKey:
        key = serialization.load_pem_public_key(pem_text.encode("utf-8"))
        if not isinstance(key, Ed25519PublicKey):
            raise TypeError("The loaded public key is not Ed25519")
        return key

    @staticmethod
    def sign_text(private_key: Ed25519PrivateKey, text: str) -> bytes:
        return private_key.sign(text.encode("utf-8"))

    @staticmethod
    def verify_text(
        public_key: Ed25519PublicKey,
        text: str,
        signature: bytes,
    ) -> bool:
        try:
            public_key.verify(signature, text.encode("utf-8"))
            return True
        except InvalidSignature:
            return False

    @staticmethod
    def signature_to_b64(signature: bytes) -> str:
        return base64.b64encode(signature).decode("ascii")

    @staticmethod
    def _normalize_b64_padding(text: str) -> str:
        cleaned = "".join(text.strip().split())
        return cleaned + "=" * (-len(cleaned) % 4)

    @staticmethod
    def _is_pem(text: str) -> bool:
        return "BEGIN PUBLIC KEY" in text.strip()

    @staticmethod
    def signature_from_b64(signature_b64: str) -> bytes:
        cleaned = CryptoManager._normalize_b64_padding(signature_b64)
        try:
            return base64.b64decode(cleaned)
        except Exception:
            return base64.urlsafe_b64decode(cleaned)

    @staticmethod
    def signature_from_auto(signature_text: str) -> bytes:
        cleaned = CryptoManager._normalize_b64_padding(signature_text)

        # Si parece urlsafe, usa urlsafe primero
        if "-" in cleaned or "_" in cleaned:
            return base64.urlsafe_b64decode(cleaned)

        try:
            return base64.b64decode(cleaned)
        except Exception:
            return base64.urlsafe_b64decode(cleaned)

    @staticmethod
    def load_public_key_from_base64(b64_text: str) -> Ed25519PublicKey:
        cleaned = CryptoManager._normalize_b64_padding(b64_text)

        # Si parece base64url, usa urlsafe primero
        if "-" in cleaned or "_" in cleaned:
            raw = base64.urlsafe_b64decode(cleaned)
        else:
            try:
                raw = base64.b64decode(cleaned)
            except Exception:
                raw = base64.urlsafe_b64decode(cleaned)

        if len(raw) != 32:
            raise ValueError(f"Invalid Ed25519 public key length: {len(raw)} bytes")

        return Ed25519PublicKey.from_public_bytes(raw)

    @staticmethod
    def load_public_key_auto(text: str) -> Ed25519PublicKey:
        cleaned = text.strip()

        if CryptoManager._is_pem(cleaned):
            return CryptoManager.load_public_key_from_pem_text(cleaned)

        return CryptoManager.load_public_key_from_base64(cleaned)

    @staticmethod
    def detect_key_format(text: str) -> str:
        cleaned = text.strip()

        if "BEGIN PUBLIC KEY" in cleaned:
            return "pem"

        if "-" in cleaned or "_" in cleaned:
            return "base64url"

        return "base64"

    @staticmethod
    def short_hash_id(text: str, signature: bytes, size: int = 10) -> str:
        digest = hashlib.sha256(text.encode("utf-8") + signature).digest()
        return base64.b32encode(digest[:8]).decode("ascii").rstrip("=")[:size]

    @staticmethod
    def verify_hash_id(
        text: str,
        signature: bytes,
        hash_id: str,
        size: int = 10,
    ) -> bool:
        expected = CryptoManager.short_hash_id(text, signature, size=size)
        return expected.strip().upper() == hash_id.strip().upper()