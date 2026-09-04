from pathlib import Path
import os
import re
import shutil
import tempfile
import zipfile

MAX_ARCHIVE_BYTES = 20 * 1024 * 1024
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_FILES = 500
MAX_TOTAL_EXTRACTED = 20 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".c", ".h", ".cpp", ".hpp",
    ".cs", ".go", ".rs", ".rb", ".php", ".html", ".css", ".md", ".txt",
    ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".xml", ".sql",
    ".sh", ".bat"
}
SECRET_NAMES = {
    ".env", ".env.local", ".env.production", ".npmrc", ".pypirc",
    "id_rsa", "id_ed25519", "credentials", "credentials.json"
}

def _is_secret_name(name: str) -> bool:
    base = Path(name).name.lower()
    return base in SECRET_NAMES or base.startswith(".env.")

def _is_text_file(data: bytes) -> bool:
    if b"\x00" in data:
        return False
    try:
        data.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False

def extract_zip_safely(uploaded_file) -> Path:
    if uploaded_file.size > MAX_ARCHIVE_BYTES:
        raise ValueError("Archive is too large.")
    tmp = Path(tempfile.mkdtemp(prefix="reporadar_"))
    try:
        with zipfile.ZipFile(uploaded_file) as z:
            infos = z.infolist()
            if len(infos) > MAX_FILES:
                raise ValueError("Archive contains too many files.")
            total = 0
            for info in infos:
                name = info.filename.replace("\\", "/")
                if not name or name.endswith("/"):
                    continue
                if name.startswith("/") or re.match(r"^[A-Za-z]:/", name):
                    raise ValueError(f"Absolute path rejected: {name}")
                if any(part == ".." for part in Path(name).parts):
                    raise ValueError(f"Parent traversal rejected: {name}")
                if _is_secret_name(name):
                    raise ValueError(f"Potential secrets file rejected: {name}")
                if info.file_size > MAX_FILE_BYTES:
                    raise ValueError(f"File too large: {name}")
                if Path(name).suffix.lower() not in ALLOWED_EXTENSIONS:
                    raise ValueError(f"Unsupported file type: {name}")
                mode = (info.external_attr >> 16) & 0o170000
                if mode == 0o120000:
                    raise ValueError(f"Symlink rejected: {name}")
                total += info.file_size
                if total > MAX_TOTAL_EXTRACTED:
                    raise ValueError("Total extracted content exceeds limit.")
            for info in infos:
                if info.filename.endswith("/"):
                    continue
                data = z.read(info)
                if not _is_text_file(data):
                    raise ValueError(f"Binary or non-UTF-8 file rejected: {info.filename}")
                target = tmp / info.filename
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
        return tmp
    except Exception:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
