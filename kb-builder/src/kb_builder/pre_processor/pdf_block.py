from dataclasses import dataclass
from typing import *

@dataclass
class PdfRegion:
    page_number: Optional[int]
    vertical_position: Optional[float] = None
    horizontal_position: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    image_url: Optional[str] = None


@dataclass
class PDFBlock:
    text: str
    type: str
    region: PdfRegion
