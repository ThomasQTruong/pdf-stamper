"""Stamp asset management for the PDF Stamper application.

This module provides the Stamp class, which represents a stamp image asset.
It handles loading image dimensions and calculating the total stamp size
including user-defined padding.
"""

from dataclasses import dataclass, field
from pathlib import Path
from PIL import Image, UnidentifiedImageError


@dataclass
class Stamp:
    """Represents the stamp image and its calculated dimensions."""

    stamp_path: Path
    padding: float
    width: float = field(init=False, default=0.0)
    height: float = field(init=False, default=0.0)

    def __post_init__(self):
        """Initialize the stamp and calculate dimensions."""
        try:
            with Image.open(self.stamp_path) as img:
                w, h = img.size
                self.width = w + (self.padding * 2)  # Left and right padding.
                self.height = h + (self.padding * 2)  # Top and bottom padding.
        except (FileNotFoundError, UnidentifiedImageError, OSError):
            pass
