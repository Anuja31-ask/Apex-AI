import hashlib
import uuid


def compute_sha256(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()


def generate_stored_filename(extension: str) -> str:
    return f"{uuid.uuid4()}.{extension}"