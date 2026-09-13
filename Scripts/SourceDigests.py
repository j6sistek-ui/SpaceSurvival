"""Compare reviewed source hashes without confusing Git newline serialization.

Raw bytes remain authoritative. Only UTF-8 OBJ, MTL and JSON text may match the
other complete LF/CRLF representation. Nothing strips whitespace, parses JSON,
changes mixed line endings, normalizes binaries or rewrites recorded hashes.
"""
import hashlib
from pathlib import Path

TEXT_SUFFIXES = frozenset((".obj", ".mtl", ".json"))


def representations(path, data):
    """Return raw bytes and, when eligible, the single alternate serialization."""
    if Path(path).suffix.lower() not in TEXT_SUFFIXES or b"\0" in data:
        return (data,)
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return (data,)
    if b"\r" in data:
        remainder = data.replace(b"\r\n", b"")
        if b"\r" in remainder or b"\n" in remainder:
            return (data,)
        return (data, data.replace(b"\r\n", b"\n"))
    if b"\n" in data:
        return (data, data.replace(b"\n", b"\r\n"))
    return (data,)


def matches(path, expected_sha256):
    """Check exact reviewed bytes, with only the documented text exception."""
    if not isinstance(expected_sha256, str) or len(expected_sha256) != 64:
        return False
    expected = expected_sha256.lower()
    if any(character not in "0123456789abcdef" for character in expected):
        return False
    source = Path(path)
    data = source.read_bytes()
    return any(hashlib.sha256(value).hexdigest() == expected
               for value in representations(source, data))
