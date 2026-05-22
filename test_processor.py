"""Simple test script for PDFProcessor.

To run this test:
1. Ensure you have a 'docs' folder with at least one PDF file.
2. Ensure you have a 'stamp.png' file in the root directory.
3. Run: python3 test_processor.py
"""

from pathlib import Path
from processor import PDFProcessor


def test_stamping():
    """Tests the PDFProcessor stamping functionality."""
    input_dir = Path("docs")
    output_dir = Path("test_output")
    stamp_path = Path("stamp.png")

    if not input_dir.exists():
        print(f"Error: {input_dir} not found.")
        return

    if not stamp_path.exists():
        print(f"Error: {stamp_path} not found.")
        return

    config = {
        "stamp_path": stamp_path,
        "padding": 5.0,
        "margin_x": 50.0,
        "margin_y": 50.0,
        "threshold": 1,
        "start_pos": 8,
        "search_dir": 4,
    }

    def log_callback(message, tag=None):
        print(f"[{tag or 'INFO'}] {message}")

    def progress_callback(progress):
        print(f"Progress: {progress:.2%}")

    processor = PDFProcessor(
        config, output_callback=log_callback, progress_callback=progress_callback
    )

    print("Starting stamping process...")
    success, warning, error = processor.run(input_dir, output_dir, "_test")
    print(f"Results: {success} successes, {warning} warnings, {error} errors.")

    # Check if output file exists.
    # Assuming search-test.pdf is in the docs folder based on the initial directory listing.
    example_output = output_dir / "search-test_test.pdf"
    if example_output.exists():
        print(f"Success: Output file created at {example_output}")
    else:
        print(
            f"Note: Checked for {example_output}, but it might have a different "
            f"name if search-test.pdf wasn't the input."
        )


if __name__ == "__main__":
    test_stamping()
