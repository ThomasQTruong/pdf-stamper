"""Simple test script for PDFProcessor.

To run this test:
1. Ensure you have a 'docs' folder with at least one PDF file.
2. Ensure you have a 'stamp.png' file in the root directory.
3. Run: python3 test_processor.py
"""

from pathlib import Path
import pytest
from pdf_stamper.processor import PDFProcessor  # pylint: disable=import-error


def test_stamping_process(tmp_path):
    """Tests the PDFProcessor stamping functionality using pytest."""
    # Setup paths
    input_dir = Path("docs")
    output_dir = tmp_path / "test_output"
    output_dir.mkdir()
    stamp_path = Path("stamp.png")

    # Skip if environment isn't ready
    if not input_dir.exists() or not stamp_path.exists():
        pytest.skip("Test resources (docs/ or stamp.png) not found.")

    config = {
        "stamp_path": stamp_path,
        "padding": 5.0,
        "margin_x": 50.0,
        "margin_y": 50.0,
        "threshold": 1,
        "start_pos": 8,
        "search_dir": 4,
    }

    processor = PDFProcessor(
        config, output_callback=lambda m, t: None, progress_callback=lambda p: None
    )

    success, warning, error = processor.run(input_dir, output_dir, "_test")

    # Assertions: pytest checks these and reports failures
    assert success > 0, "No files were successfully stamped"
    assert error == 0, f"Encountered {error} errors during stamping"

    # Check if at least one expected file exists
    # (Assuming search-test.pdf is in docs/ based on your initial file list)
    expected_file = output_dir / "search-test_test.pdf"
    assert (
        expected_file.exists()
    ), f"Expected output file {expected_file.name} was not created"
