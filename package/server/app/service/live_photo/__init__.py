from typing import List, Optional
from .base import LivePhotoParser
from .apple import AppleLivePhotoParser
from .android import AndroidLivePhotoParser
from .vivo import VivoLivePhotoParser



class LivePhotoService:
    def __init__(self):
        self.parsers: List[LivePhotoParser] = [
            AppleLivePhotoParser(),
            AndroidLivePhotoParser(),
            VivoLivePhotoParser()
        ]

    def get_content_identifier(self, file_path: str) -> Optional[str]:
        for parser in self.parsers:
            if parser.is_supported(file_path):
                cid = parser.parse(file_path)
                if cid:
                    return cid
        return None

live_photo_service = LivePhotoService()
