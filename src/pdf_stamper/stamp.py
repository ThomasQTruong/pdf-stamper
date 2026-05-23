from PIL import Image


class Stamp:
    def __init__(self, stamp_path, padding):
        """Initialize the stamp and store the stamp's data."""
        try:
            with Image.open(stamp_path) as self.stamp:
                self.width, self.height = self.stamp.size
                self.width += padding * 2  # Left and right padding.
                self.height += padding * 2  # Top and bottom padding.
                self.padding = padding
        except FileNotFoundError:
            self.stamp = None
            self.width = 0
            self.height = 0
            self.padding = 0
