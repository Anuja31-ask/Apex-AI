import magic

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
}

MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB


class FileValidationError(Exception):
    def __init__(self, reason: str, event_type: str):
        self.reason = reason
        self.event_type = event_type
        super().__init__(reason)


def validate_extension(filename: str) -> str:
    if "." not in filename:
        raise FileValidationError("File has no extension", "INVALID_FILE_SIGNATURE")

    parts = filename.rsplit(".", 1)
    extension = parts[1].lower()

    if filename.count(".") > 1:
        suspicious_middle = parts[0]
        if any(suspicious_middle.lower().endswith(ext) for ext in ["exe", "sh", "bat", "php", "js"]):
            raise FileValidationError("Double extension detected", "SUSPICIOUS_UPLOAD")

    if extension not in ALLOWED_EXTENSIONS:
        raise FileValidationError(f"Extension .{extension} not allowed", "INVALID_FILE_SIGNATURE")

    return extension


def validate_size(file_bytes: bytes) -> int:
    size = len(file_bytes)
    if size == 0:
        raise FileValidationError("Empty file", "INVALID_FILE_SIGNATURE")
    if size > MAX_FILE_SIZE_BYTES:
        raise FileValidationError("File exceeds maximum allowed size", "FILE_TOO_LARGE")
    return size


def validate_magic_bytes(file_bytes: bytes) -> str:
    detected_mime = magic.from_buffer(file_bytes, mime=True)
    if detected_mime not in ALLOWED_MIME_TYPES:
        raise FileValidationError(
            f"File content does not match an allowed type (detected: {detected_mime})",
            "INVALID_FILE_SIGNATURE",
        )
    return detected_mime


def validate_safe_filename(filename: str) -> None:
    if ".." in filename or "/" in filename or "\\" in filename:
        raise FileValidationError("Filename contains path traversal characters", "PATH_TRAVERSAL_ATTEMPT")
