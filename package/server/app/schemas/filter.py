from typing import List, Optional
from pydantic import BaseModel

class FilterOptions(BaseModel):
    years: List[int]
    cities: List[str]
    makes: List[str]
    models: List[str]
    image_types: List[str]
    file_types: List[str]
