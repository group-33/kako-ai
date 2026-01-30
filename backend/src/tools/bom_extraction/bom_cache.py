from __future__ import annotations

import os
import pickle
import tempfile
from typing import Optional
from filelock import FileLock
import cv2
import hashlib


class BOMCache:
    """
    Minimal pickled dict cache for BOMs. Stores only the full (pre-enrichment) BOM as a dict.

    If initialized with enabled=False the cache acts as a no-op in order to keep
    caller code simple (no need to check config flags everywhere).
    """

    def __init__(
        self, path: Optional[str] = None, lock_timeout: int = 10, enabled: bool = True
    ):
        self.enabled = bool(enabled)
        self.path = os.path.expanduser(path or "~/.kakoai/bom_cache.pkl")
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self.lock = FileLock(self.path + ".lock", timeout=lock_timeout)

    def _load(self) -> dict:
        if not os.path.exists(self.path):
            return {}
        with self.lock:
            try:
                with open(self.path, "rb") as f:
                    return pickle.load(f) or {}
            except Exception:
                return {}

    def _atomic_write(self, data: dict):
        dirn = os.path.dirname(self.path)
        fd, tmp = tempfile.mkstemp(dir=dirn)
        os.close(fd)
        with open(tmp, "wb") as f:
            pickle.dump(data, f)
        os.replace(tmp, self.path)

    def _get(self, key: str):
        if not self.enabled:
            return None
        d = self._load()
        return d.get(key)

    def _set(self, key: str, value):
        if not self.enabled:
            return
        d = self._load()
        d[key] = value
        self._atomic_write(d)

    def is_in_cache(self, image_path: str) -> bool:
        """Return True if a full BOM for the normalized image is present in the cache."""
        if not self.enabled:
            return False
        key = self.compute_image_hash(image_path)
        return self._get(key) is not None

    def get_full_bom(self, image_path: str):
        """Return the stored full (pre-enrichment) BOM dict for the image, or None."""
        if not self.enabled:
            return None
        key = self.compute_image_hash(image_path)
        return self._get(key)

    def set_full_bom(self, image_path: str, value):
        """Store the full (pre-enrichment) BOM for the normalized image."""
        if not self.enabled:
            return
        key = self.compute_image_hash(image_path)
        self._set(key, value)

    def compute_image_hash(self, image_path: str) -> str:
        """Compute a stable SHA256 hash for the normalized image.

        Preference: re-encode the loaded image to PNG to avoid differences in metadata.
        Fallback: hash raw file bytes if OpenCV cannot read the image.
        """
        try:
            img = cv2.imread(image_path)
            if img is not None:
                _, buf = cv2.imencode(".png", img, [cv2.IMWRITE_PNG_COMPRESSION, 3])
                return hashlib.sha256(buf.tobytes()).hexdigest()
        except Exception:
            pass

        with open(image_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
