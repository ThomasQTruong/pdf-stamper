"""Handles all PDF processing logic for the PDF Stamper application."""

import math
import pymupdf
from PIL import Image


class PDFProcessor:
    """Handles the PDF stamping logic, separate from the GUI.

    Args:
        config (dict): A dictionary containing stamping parameters:
            - 'stamp_path' (Path): Path to the stamp image.
            - 'padding' (float): Spacing around the stamp.
            - 'margin_x' (float): Horizontal margin from page edges.
            - 'margin_y' (float): Vertical margin from page edges.
            - 'threshold' (int): Search threshold for finding empty space.
            - 'start_pos' (int): Starting grid position (0-8).
            - 'search_dir' (int): Search direction grid index (0-8).
        output_callback (callable, optional): Function to log messages.
            Expected signature: func(message, tag=None).
        progress_callback (callable, optional): Function to update progress.
            Expected signature: func(percentage_float).
    """

    def __init__(self, config, output_callback=None, progress_callback=None):
        """Initializes the PDFProcessor with configuration and callbacks."""
        self.config = config
        self.output_callback = output_callback
        self.progress_callback = progress_callback
        self.current_progress = 0

    def run(self, input_dir, output_dir, append_value):
        """Orchestrates the stamping process for all files in the input directory.

        Args:
            input_dir (Path): Path to the directory containing PDFs to stamp.
            output_dir (Path): Path to the directory where stamped PDFs will be saved.
            append_value (str): String to append to the output filename.

        Returns:
            tuple: A tuple containing (success_count, warning_count, error_count).
        """
        success_count = 0
        warning_count = 0
        error_count = 0

        # For each pdf in the target directory.
        self.current_progress = 0
        progress_total = self.get_progress_total(input_dir)

        for pdf in input_dir.iterdir():
            # Going through the file, add 1 to progress.
            self.current_progress += 1

            # If it is not a file, skip it.
            if not pdf.is_file():
                warning_count += 1
                if self.output_callback:
                    self.output_callback(
                        f"[WARNING] {pdf.name}: skipped, not a valid file.", "warning"
                    )
                continue

            # Grab output directory and create if it doesnt exist.
            output_dir.mkdir(parents=True, exist_ok=True)

            # Customize the output name.
            output_name = pdf.stem + append_value + pdf.suffix
            output_pdf = output_dir / output_name

            # Add the stamp to the pdf.
            success = self.add_stamp(pdf, output_pdf, progress_total)
            if success == 1:
                # Returned 1, there was an error.
                error_count += 1
            elif success == 2:
                # Returned 2, there was a warning.
                warning_count += 1
            else:
                success_count += 1

        return success_count, warning_count, error_count

    def add_stamp(self, input_pdf, output_pdf, progress_total):
        """Stamps all pages of a single PDF file.

        Args:
            input_pdf (Path): Path to the source PDF file.
            output_pdf (Path): Path where the stamped PDF will be saved.
            progress_total (int): Total steps for progress bar calculation.

        Returns:
            int: 0 if success, 1 if error, 2 if warning.
        """
        # Open the pdf with pymupdf.
        try:
            doc = pymupdf.open(input_pdf)
        except (pymupdf.FileDataError, pymupdf.EmptyFileError):
            if self.output_callback:
                self.output_callback(
                    f"[ERROR] {input_pdf.name}: could not open PDF.", "error"
                )
            return 1

        try:
            with Image.open(self.config["stamp_path"]) as img:
                stamp_width, stamp_height = img.size
                stamp_width += self.config["padding"] * 2  # Left and right padding.
                stamp_height += self.config["padding"] * 2  # Top and bottom padding.
        except FileNotFoundError:
            if self.output_callback:
                self.output_callback(
                    f"[Error] '{self.config['stamp_path']}' is missing!", "error"
                )
            doc.close()
            return 1

        for page_num in range(1, len(doc) + 1):
            # Update progress.
            self.current_progress += 1
            if self.progress_callback:
                self.progress_callback(self.current_progress / progress_total)

            # PDF page indices start at 0.
            page = doc[page_num - 1]

            # Obtain page dimensions and top-left values.
            br = page.rect.br
            x0 = self.config["margin_x"]
            y0 = self.config["margin_y"]
            x1 = x0 + stamp_width
            y1 = y0 + stamp_height
            start_row = int(self.config["start_pos"] / 3)
            start_column = self.config["start_pos"] % 3

            # Set x-value based on column.
            if start_column == 1:
                # Middle column, center the stamp.
                x0 = (br.x - stamp_width) / 2
                x1 = x0 + stamp_width
            elif start_column == 2:
                # Right column.
                x0 = br.x - self.config["margin_x"] - stamp_width
                x1 = br.x - self.config["margin_x"]

            # Set y-value based on row.
            if start_row == 1:
                # Middle row.
                y0 = (br.y - stamp_height) / 2
                y1 = y0 + stamp_height
            elif start_row == 2:
                # Bottom row.
                y0 = br.y - self.config["margin_y"] - stamp_height
                y1 = br.y - self.config["margin_y"]

            # Check margin x/y values.
            if self.is_out_of_bounds(x0, x1, br.x, self.config["margin_x"]):
                if self.output_callback:
                    self.output_callback(
                        f"[Skipped] Out of Bounds: marginX ({self.config['margin_x']})"
                        f" or stamp width ({stamp_width}) is too high for"
                        + f" the page width ({br.x})!",
                        "warning",
                    )
                doc.close()
                return 2
            if self.is_out_of_bounds(y0, y1, br.y, self.config["margin_y"]):
                if self.output_callback:
                    self.output_callback(
                        f"[Skipped] Out of Bounds: marginY ({self.config['margin_y']})"
                        + f" or stamp height ({stamp_height}) is too high for"
                        + f" the page height ({br.y})!",
                        "warning",
                    )
                doc.close()
                return 2

            rect = pymupdf.Rect(x0, y0, x1, y1)
            # Search is enabled.
            if self.config["threshold"] > 0:
                if self.config["search_dir"] == 4:
                    # Search all of the directions.
                    rect = self.search_all(page, rect)
                else:
                    # Search normally.
                    rect = self.search(page, rect, br, stamp_width, stamp_height)

            # Clean the padding off before stamping for a centered insertion.
            offset = self.config["padding"] / 2
            clean_rect = pymupdf.Rect(
                rect.x0 + offset, rect.y0 + offset, rect.x1 - offset, rect.y1 - offset
            )
            page.insert_image(clean_rect, filename=self.config["stamp_path"])

        doc.save(output_pdf)
        doc.close()
        return 0

    def search(self, page, rect, br, stamp_width, stamp_height):
        """Searches for an empty spot to stamp at the selected direction.

        Args:
            page (pymupdf.Page): The document page to search on.
            rect (pymupdf.Rect): The rectangle where the stamp goes.
            br (pymupdf.Point): The bottom-right point of the page.
            stamp_width (float): The width of the stamp including padding.
            stamp_height (float): The height of the stamp including padding.

        Returns:
            pymupdf.Rect: The rect with the found position, else original rect.
        """
        text_in_rect = page.get_text("text", clip=rect)
        # Empty spot at the location already.
        if not text_in_rect.strip():
            return rect

        search_row = int(self.config["search_dir"] / 3)
        search_column = self.config["search_dir"] % 3

        # Calculate threshold based on direction.
        threshold_x = self.config["threshold"]
        if search_column == 0:  # Left column.
            threshold_x *= -1
        elif search_column % 3 == 1:  # Middle column.
            threshold_x = 0

        threshold_y = self.config["threshold"]
        if search_row == 0:  # Top row.
            threshold_y *= -1
        elif search_row == 1:  # Middle row.
            threshold_y = 0

        # Diagonal search.
        if self.config["search_dir"] % 2 == 0:
            # Figure out the end point.
            end_x = self.config["margin_x"]
            end_y = self.config["margin_y"]
            if search_column == 1:
                # Middle column.
                end_x = rect.x0
            elif search_column == 2:
                # Right column.
                end_x = br.x - self.config["margin_x"] - stamp_width

            if search_row == 1:
                end_y = rect.y0
            elif search_row == 2:
                # Bottom row.
                end_y = br.y - self.config["margin_y"] - stamp_height

            # Calculate the hypotenuse.
            dx = end_x - rect.x0
            dy = end_y - rect.y0
            distance = math.hypot(dx, dy)

            # No distance to move, return original.
            if distance == 0:
                return rect

            # Apply to threshold.
            threshold_x = (dx / distance) * self.config["threshold"]
            threshold_y = (dy / distance) * self.config["threshold"]

        # Obtain all the words in the search rect.
        words = page.get_text("words")
        # Extract the positions from the word and make a rect with it.
        word_rects = [pymupdf.Rect(w[:4]) for w in words if w[4].strip()]

        # Search for a free slot using the selected direction.
        search_x0 = rect.x0 + threshold_x
        search_y0 = rect.y0 + threshold_y
        search_x1 = rect.x1 + threshold_x
        search_y1 = rect.y1 + threshold_y
        while not self.is_out_of_bounds(
            search_x0, search_x1, br.x, self.config["margin_x"]
        ) and not self.is_out_of_bounds(
            search_y0, search_y1, br.y, self.config["margin_y"]
        ):
            search_rect = pymupdf.Rect(search_x0, search_y0, search_x1, search_y1)

            collide = next(
                (word for word in word_rects if search_rect.intersects(word)), None
            )

            # No collision! This is a valid spot.
            if not collide:
                return search_rect

            # Searching a cardinal direction.
            if self.config["search_dir"] == 1:
                # Searching up.
                search_x0 += threshold_x
                search_x1 += threshold_x
                search_y0 = search_y0 - stamp_height
                search_y1 = collide.y0 - self.config["threshold"]
            elif self.config["search_dir"] == 3:
                # Searching left.
                search_x0 = search_x0 - stamp_width
                search_x1 = collide.x0 - self.config["threshold"]
                search_y0 += threshold_y
                search_y1 += threshold_y
            elif self.config["search_dir"] == 5:
                # Searching right.
                search_x0 = collide.x1 + self.config["threshold"]
                search_x1 = search_x0 + stamp_width
                search_y0 += threshold_y
                search_y1 += threshold_y
            elif self.config["search_dir"] == 7:
                # Searching down.
                search_x0 += threshold_x
                search_x1 += threshold_x
                search_y0 = collide.y1 + self.config["threshold"]
                search_y1 = search_y0 + stamp_height
            else:
                search_x0 += threshold_x
                search_x1 += threshold_x
                search_y0 += threshold_y
                search_y1 += threshold_y

        # No spot found, return the original.
        return rect

    def search_all(self, page, rect):
        """Searches for an empty spot to stamp for both x and y axis.

        Args:
            page (pymupdf.Page): The document page to search on.
            rect (pymupdf.Rect): The rectangle where the stamp goes.

        Returns:
            pymupdf.Rect: The rect with the found position, else original rect.
        """
        text_in_rect = page.get_text("text", clip=rect)
        # Empty spot at the location already.
        if not text_in_rect.strip():
            return rect
        br = page.rect.br
        stamp_width = rect.x1 - rect.x0
        stamp_height = rect.y1 - rect.y0

        # Start from the top-left corner.
        search_y0 = self.config["margin_y"]
        search_y1 = search_y0 + stamp_height

        # Obtain all the words in the page.
        words = page.get_text("words")
        # Extract the positions from the word and make a rect with it.
        word_rects = [pymupdf.Rect(w[:4]) for w in words if w[4].strip()]

        # While search_rect is not out of y-axis boundary.
        while not self.is_out_of_bounds(
            search_y0, search_y1, br.y, self.config["margin_y"]
        ):
            search_x0 = self.config["margin_x"]
            search_x1 = search_x0 + stamp_width

            # While search_rect is not out of x-axis boundary.
            while not self.is_out_of_bounds(
                search_x0, search_x1, br.x, self.config["margin_x"]
            ):
                # Create the rectangle for the current test spot.
                search_rect = pymupdf.Rect(search_x0, search_y0, search_x1, search_y1)
                collide = next(
                    (word for word in word_rects if search_rect.intersects(word)), None
                )

                # No collision! This is a valid spot.
                if not collide:
                    return search_rect

                # Move right by the threshold
                search_x0 = collide.x1 + self.config["threshold"]
                search_x1 = search_x0 + stamp_width

            # Move down to the next row by the threshold
            search_y0 += self.config["threshold"]
            search_y1 += self.config["threshold"]

        # No spot found, return original.
        return rect

    def is_out_of_bounds(self, pos0, pos1, max_size, margin):
        """Determines whether the box coordinates are outside of the page bound.

        Args:
            pos0 (float): the x0/y0 coordinate of the box.
            pos1 (float): the x1/y1 coordinate of the box.
            max_size (float): the page height/width.
            margin (float): the inner-distance away from the edge.

        Returns:
            bool: True if the rect is out of bounds, False otherwise.
        """
        return pos0 < margin or pos1 > max_size - margin

    def get_progress_total(self, input_dir):
        """Retrives the progress total (file count + pages).

        Args:
            input_dir (Path): The input directory's path.

        Returns:
            int: The progress total.
        """
        # Create a list of files.
        files = list(input_dir.iterdir())

        # Sum up all pages.
        total_pages = 0
        for file in files:
            try:
                # If it is a pdf file.
                if file.is_file() and file.suffix.lower() == ".pdf":
                    # Add to sum.
                    with pymupdf.open(file) as doc:
                        total_pages += len(doc)
            except (pymupdf.FileDataError, pymupdf.EmptyFileError):
                continue  # Skip corrupted PDFs

        return len(files) + total_pages
