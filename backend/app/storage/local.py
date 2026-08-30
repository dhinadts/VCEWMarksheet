import os
from pathlib import Path


class LocalDocumentStorage:
    """Private local storage; files are never mounted as public static assets."""

    def __init__(self, root: str | os.PathLike[str]) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def upload(self, key: str, content: bytes) -> Path:
        target = (self.root / key).resolve()
        if self.root not in target.parents:
            raise ValueError("Invalid storage key")
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_bytes(content)
        temporary.replace(target)
        return target

    def download(self, key: str) -> bytes:
        target = (self.root / key).resolve()
        if self.root not in target.parents or not target.is_file():
            raise FileNotFoundError("Stored document was not found")
        return target.read_bytes()

    def delete(self, key: str) -> None:
        target = (self.root / key).resolve()
        if self.root in target.parents and target.is_file():
            target.unlink()
