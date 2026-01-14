import os
import re
from typing import Optional
from .base import LivePhotoParser

class AppleLivePhotoParser(LivePhotoParser):
    def is_supported(self, file_path: str) -> bool:
        ext = os.path.splitext(file_path)[1].lower()
        return ext in ['.heic']

    def parse(self, file_path: str) -> Optional[str]:
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.heic', '.jpg', '.jpeg']:
            return self._parse_image(file_path)
        elif ext in ['.mov', '.mp4']:
            return self._parse_video(file_path)
        return None

    def _parse_image(self, file_path: str) -> Optional[str]:
        try:
            with open(file_path, 'rb') as f:
                # Read first 100KB. XMP/Metadata is usually early.
                head = f.read(100 * 1024)
                
                # UUID pattern: 8-4-4-4-12 hex digits
                uuid_pattern = b'[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}'
                
                # Apple often uses "ContentIdentifier" in XMP
                # Search for ContentIdentifier="UUID" or >UUID< near ContentIdentifier
                
                # Strategy 1: Look for explicit key-value
                match = re.search(b'ContentIdentifier=["\']?(' + uuid_pattern + b')["\']?', head, re.IGNORECASE)
                if match:
                    return match.group(1).decode('utf-8')
                
                # Strategy 2: Look for the UUID near the key "apple-fi:ContentIdentifier"
                key = b'apple-fi:ContentIdentifier'
                if key in head:
                    idx = head.find(key)
                    snippet = head[idx:idx+200]
                    m = re.search(uuid_pattern, snippet, re.IGNORECASE)
                    if m:
                        return m.group(0).decode('utf-8')

        except Exception:
            pass
        return None

    def _parse_video(self, file_path: str) -> Optional[str]:
        try:
            key = b'com.apple.quicktime.content.identifier'
            uuid_pattern = b'[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}'
            
            with open(file_path, 'rb') as f:
                # Search head
                head = f.read(100 * 1024)
                if key in head:
                    idx = head.find(key)
                    # The value is usually shortly after the key in the atom
                    snippet = head[idx:idx+200]
                    m = re.search(uuid_pattern, snippet, re.IGNORECASE)
                    if m:
                        return m.group(0).decode('utf-8')

                # Search tail (metadata often at the end for MOV)
                f.seek(0, 2)
                size = f.tell()
                read_size = min(size, 100 * 1024)
                if read_size > 0:
                    f.seek(-read_size, 2)
                    tail = f.read(read_size)
                    if key in tail:
                        idx = tail.find(key)
                        snippet = tail[idx:idx+200]
                        m = re.search(uuid_pattern, snippet, re.IGNORECASE)
                        if m:
                            return m.group(0).decode('utf-8')
        except Exception:
            pass
        return None
