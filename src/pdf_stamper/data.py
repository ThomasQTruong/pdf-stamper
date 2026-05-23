"""Configuration management for the PDF Stamper application.

This module provides the Data class, a centralized container for application
settings. It handles default values, JSON-based persistence, and path
normalization for both the GUI and CLI versions of the tool.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path


# pylint: disable=too-many-instance-attributes
@dataclass
class Data:
    """Stores and manages stamper settings using a modern dataclass."""

    # File and Path Settings
    stamp: Path = field(default_factory=lambda: Path.cwd() / "stamp.png")
    input_dir: Path = field(default_factory=lambda: Path.cwd() / "docs")
    output_dir: Path = field(default_factory=lambda: Path.cwd() / "output")
    append: str = ""

    # Stamping Logic Settings
    padding: float = 5.0
    margin_x: float = 20.0
    margin_y: float = 20.0
    threshold: int = 1
    start_pos: int = 8  # 3x3 grid index
    search_dir: int = 1  # 3x3 grid index

    def __post_init__(self):
        """Automatically called after initialization; used here to load saved config."""
        self.load_config()

    def load_config(self):
        """Loads settings from the json config file if it exists."""
        config_path = Path("stamper-config.json")
        if not config_path.exists():
            return

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                settings = json.load(f)

                # Update attributes. We use a mapping to handle name differences
                # between your JSON keys (marginX) and Python attributes (margin_x).
                mapping = {
                    "stamp_path": "stamp",
                    "input_dir": "input_dir",
                    "output_dir": "output_dir",
                    "append": "append",
                    "padding": "padding",
                    "marginX": "margin_x",
                    "marginY": "margin_y",
                    "threshold": "threshold",
                    "start_pos": "start_pos",
                    "search_dir": "search_dir",
                }

                for json_key, attr_name in mapping.items():
                    if json_key in settings:
                        value = settings[json_key]
                        # Ensure path strings are converted back to Path objects
                        if attr_name in ["stamp", "input_dir", "output_dir"]:
                            value = Path(value)
                        setattr(self, attr_name, value)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: Could not load config: {e}")

    def save_config(self):
        """Saves the current settings to a json file."""
        # We manually build the dict to keep your specific JSON key names (like marginX)
        data = {
            "stamp_path": str(self.stamp),
            "input_dir": str(self.input_dir),
            "output_dir": str(self.output_dir),
            "append": self.append,
            "padding": self.padding,
            "marginX": self.margin_x,
            "marginY": self.margin_y,
            "threshold": self.threshold,
            "start_pos": self.start_pos,
            "search_dir": self.search_dir,
        }
        with open("stamper-config.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
