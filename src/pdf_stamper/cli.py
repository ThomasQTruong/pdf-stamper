"""Command-line interface for the PDF Stamper application.

This module provides a CLI wrapper around the PDFProcessor logic, allowing users
to mass-stamp PDFs from the terminal using command-line arguments.
"""

import argparse
import sys
from pathlib import Path
from pdf_stamper.processor import PDFProcessor
from pdf_stamper.data import Data


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Mass stamp PDF files in a directory.")

    # File and Path Arguments
    parser.add_argument(
        "--stamp", type=str, help="Path to the stamp image (default: stamp.png)"
    )
    parser.add_argument(
        "--input", type=str, help="Path to input directory (default: docs/)"
    )
    parser.add_argument(
        "--output", type=str, help="Path to output directory (default: output/)"
    )
    parser.add_argument(
        "--append", type=str, help="String to append to filenames (default: none)"
    )

    # Stamping Logic Arguments
    parser.add_argument(
        "--padding", type=float, help="Spacing around the stamp (default: 5.0)"
    )
    parser.add_argument(
        "--margin-x", type=float, help="X-axis margin from edges (default: 20.0)"
    )
    parser.add_argument(
        "--margin-y", type=float, help="Y-axis margin from edges (default: 20.0)"
    )
    parser.add_argument(
        "--threshold",
        type=int,
        help="Search threshold (1+ enables search, 0 disables) (default: 1)",
    )
    parser.add_argument(
        "--pos",
        type=int,
        choices=range(9),
        help="Starting grid position 0-8 (default: 8/Bottom-Right)",
    )
    parser.add_argument(
        "--dir",
        type=int,
        choices=range(9),
        help="Search direction grid index 0-8 (default: 1/Up)",
    )

    args = parser.parse_args()

    # Initialize data with defaults (loads from config file if exists)
    data = Data()

    # Override defaults with CLI arguments if provided
    if args.stamp:
        data.stamp_path = Path(Path.cwd() / args.stamp)
    if args.input:
        data.input_dir = Path(Path.cwd() / args.input)
    if args.output:
        data.output_dir = Path(Path.cwd() / args.output)
    if args.append is not None:
        data.append = args.append
    if args.padding is not None:
        data.padding = args.padding
    if args.margin_x is not None:
        data.margin_x = args.margin_x
    if args.margin_y is not None:
        data.margin_y = args.margin_y
    if args.threshold is not None:
        data.threshold = args.threshold
    if args.pos is not None:
        data.start_pos = args.pos
    if args.dir is not None:
        data.search_dir = args.dir

    if not data.input_dir.exists():
        print(f"[ERROR] '{data.input_dir}' directory cant be found.")
        sys.exit(1)

    # Initialize the processor
    processor = PDFProcessor(
        data,
        output_callback=lambda msg, tag=None: print(msg),
        progress_callback=lambda p: print(f"Progress: {p*100:.1f}%", end="\r"),
    )

    print(f"Stamping PDFs from: {data.input_dir}")
    print(f"Using stamp: {data.stamp_path}")

    success, warning, error = processor.run(
        data.input_dir, data.output_dir, data.append
    )

    print(
        f"\nFinished stamping {success} files with {warning} skipped and {error} errors."
    )


if __name__ == "__main__":
    main()
