import os
import re
from typing import Optional
from .base import LivePhotoParser

class AndroidLivePhotoParser(LivePhotoParser):
    def is_supported(self, file_path: str) -> bool:
        ext = os.path.splitext(file_path)[1].lower()
        return ext in ['.jpg', '.jpeg', '.mov', '.mp4']

    def parse(self, file_path: str) -> Optional[str]:
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.jpg', '.jpeg']:
            return self._parse_image(file_path)
        elif ext in ['.mov', '.mp4']:
            return self._parse_video(file_path)
        return None

    def _parse_image(self, file_path: str) -> Optional[str]:
        return file_path.replace('.jpg', '').replace('.jpeg', '')

    def _parse_video(self, file_path: str) -> Optional[str]:
        return file_path.replace('.mov', '').replace('.mp4', '')
