import io
import zipfile
import pytest
from src.security import extract_zip_safely

def make_zip(name, data):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(name, data)
    buf.seek(0)
    return buf

def test_rejects_traversal():
    with pytest.raises(ValueError):
        extract_zip_safely(make_zip("../evil.py", "print(1)"))

def test_rejects_secret_file():
    with pytest.raises(ValueError):
        extract_zip_safely(make_zip(".env", "TOKEN=secret"))

def test_rejects_binary():
    with pytest.raises(ValueError):
        extract_zip_safely(make_zip("image.py", b"\x00\x01\x02"))
