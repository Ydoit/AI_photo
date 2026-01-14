from abc import ABC, abstractmethod
from typing import Optional, Tuple

class LivePhotoParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> Optional[str]:
        """
        Parse the file to extract the Live Photo Content Identifier.
        :param file_path: Path to the file (image or video)
        :return: The content identifier string if found, otherwise None.
        """
        pass

    @abstractmethod
    def is_supported(self, file_path: str) -> bool:
        """
        Check if the file extension is supported by this parser.
        """
        pass
