"""Mass stamps files in a specified folder with a specified stamp img.

This program iterates through a specified input directory and stamps
all files with a specified stamp file and outputs it into a specified
output directory.
"""

import os
import sys
import threading
from tkinter import filedialog
from pathlib import Path
import customtkinter as ctk
from CTkToolTip import CTkToolTip
from PIL import Image, ImageTk
from .processor import PDFProcessor
from .data import Data


def get_resource_path(rel_path):
    """Get absolute path to resource for dev and PyInstaller."""
    try:
        base_path = sys._MEIPASS  # pylint: disable=protected-access
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, rel_path)


# pylint: disable=too-many-instance-attributes
class StamperApp(ctk.CTk):
    """
    A CustomTkinter-based GUI application for mass-stamping pdf files.

    This class inherits from the CustomTkinter class, creates the UI layout,
    and handles the file renaming logic with a visual progress bar.

    Attributes:
        data (Data): Contains all the user's settings.
        stamp_path_entry (ctk.CTkEntry): Display, shows the selected stamp file
            path (default: ./stamp.png).
        input_dir_entry (ctk.CTkEntry): Display, shows the selected input directory
            (default: ./docs/).
        output_dir_entry (ctk.CTkEntry): Input field, the directory to output the
            stamped file to (default: ./output/).
        append_entry (ctk.CTkEntry): Input field, the string to append to the output
            file.
        padding_entry (ctk.CTkEntry): Input field, the x/y axis spacing between
            the stamp and the page's texts.
        margin_x_entry (ctk.CTkEntry): Input field, the x-axis spacing of the stamp
            away from the page left/right edges.
        margin_y_entry (ctk.CTkEntry): Input field, the y-axis spacing of the stamp
            away from the page top/bottom edges.
        threshold_entry (ctk.CTkEntry): Input field, the search threshold for
            finding a whitespace to stamp (default: 1, disable = 0).
        pos_buttons (list[ctk.CTkButton]): A collection of 9 buttons representing
            the stamp position grid.
        dir_buttons (list[ctk.CTkButton]): A collection of 9 buttons representing
            the search directions grid.
        start_btn (ctk.CTkButton): Control, triggers the renaming task.
        progress_bar (ctk.CTkProgressBar): Display, shows the progress of the task.
        stamper_output (ctk.CTkTextbox): Display, shows the task log warnings,
            errors, and completion messages.
        icon (ImageTk.PhotoImage): The app icon.
        vcmd_float (str): TCL command for floating point validation.
        vcmd_int (str): TCL command for integer validation.
    """

    # App constants.
    VERSION = "2.0.0"
    FONT_FAMILY = "Segoe UI"
    SECTION_FONT = (FONT_FAMILY, 18, "bold")
    LABEL_FONT = (FONT_FAMILY, 16)  # Single-line.
    LABEL2_FONT = (FONT_FAMILY, 12)  # Multi-line / sub-header.
    BUTTON_FONT = (FONT_FAMILY, 14, "bold")  # Normal button.
    BUTTON2_FONT = (FONT_FAMILY, 10, "bold")  # Small button.
    ENTRY_FONT = (FONT_FAMILY, 16)
    PAD_X = 7  # X-axis padding.
    PAD_Y = 7  # Y-axis padding.

    def __init__(self):
        """Initialize the application window and build the UI layout."""
        super().__init__()

        # App settings.
        # Set the title of the app.
        self.title(f"PDF Stamper v{self.VERSION}")
        self.geometry("680x400")  # Set app size.
        self.resizable(0, 0)  # Make app unresizeable.
        self.after(200, self.set_app_icon)  # Set the app icon.

        # Data storage.
        self.data = Data()
        self.stamp_path_entry = None
        self.input_dir_entry = None
        self.output_dir_entry = None
        self.append_entry = None
        self.padding_entry = None
        self.threshold_entry = None
        self.margin_x_entry = None
        self.margin_y_entry = None
        self.pos_buttons = []  # Position buttons.
        self.dir_buttons = []  # Direction buttons.
        self.start_btn = None
        self.progress_bar = None
        self.stamper_output = None
        self.icon = None

        # Data validators.
        self.vcmd_float = self.register(self.validate_float)
        self.vcmd_int = self.register(self.validate_int)

        # App creation.
        self.create_settings_section()
        self.create_position_settings()
        self.create_output_section()

        # Create color tags for the text output.
        self.stamper_output.tag_config("error", foreground="#cb3f3f")  # Red
        self.stamper_output.tag_config("warning", foreground="#cf8b0c")  # Orange
        self.stamper_output.tag_config("success", foreground="#3e9b59")  # Green

        # Populate UI with loaded settings.
        self.populate_ui()

    def set_app_icon(self):
        """Sets the app icon."""
        try:
            # Obtain path to icon and set it.
            icon_path = get_resource_path("icon.png")
            if not os.path.exists(icon_path):
                icon_path = get_resource_path(
                    os.path.join(".assets", "app", "icon.png")
                )
            # User is on Windows OS.
            if sys.platform.startswith("win"):
                ico_path = icon_path.replace(".png", ".ico")
                self.iconbitmap(ico_path)
            else:
                # Not Windows OS, use a different method.
                raw_img = Image.open(icon_path)
                self.icon = ImageTk.PhotoImage(raw_img)
                self.wm_iconphoto(False, self.icon)
        except (FileNotFoundError, AttributeError):
            # App icon cant be found, ignore and leave default icon.
            pass

    def create_settings_section(self):
        """Create the Directory section of the UI."""
        # Settings title.
        settings_label = ctk.CTkLabel(
            self, text="Settings", font=self.SECTION_FONT, fg_color=("gray70", "gray30")
        )
        settings_label.pack(fill="x")
        # Settings frame.
        settings_frame = ctk.CTkFrame(self, fg_color="transparent")
        settings_frame.pack(fill="x", expand=True, padx=self.PAD_X * 2)
        settings_frame.grid_columnconfigure(0, uniform="left")
        settings_frame.grid_columnconfigure(1, weight=1)
        settings_frame.grid_columnconfigure(4)

        # Stamp path frame.
        self.stamp_path_entry = self.create_selector_section(
            settings_frame, 0, "Stamp", self.browse_file
        )
        # Input directory frame.
        self.input_dir_entry = self.create_selector_section(
            settings_frame, 1, "Input", self.browse_directory
        )
        # Output directory frame.
        self.output_dir_entry = self.create_selector_section(
            settings_frame, 2, "Output", self.browse_directory
        )

        # Append section.
        append_label = ctk.CTkLabel(
            settings_frame, text="Append:", font=self.LABEL_FONT
        )
        append_label.grid(row=3, column=0, sticky="nesw", pady=(self.PAD_Y, 0))

        extra_settings_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        extra_settings_frame.grid(row=3, column=1, sticky="nesw")
        extra_settings_frame.grid_columnconfigure(0, weight=1)
        self.append_entry = ctk.CTkEntry(
            extra_settings_frame, corner_radius=0, placeholder_text="i.e. _stamped"
        )
        self.append_entry.grid(
            row=0, column=0, sticky="nesw", padx=self.PAD_X, pady=(self.PAD_Y, 0)
        )
        # Padding settings.
        padding_label = ctk.CTkLabel(
            extra_settings_frame, text="Padding:", font=self.LABEL_FONT
        )
        padding_label.grid(
            row=0, column=1, sticky="nesw", padx=(0, self.PAD_X), pady=(self.PAD_Y, 0)
        )
        self.padding_entry = ctk.CTkEntry(
            extra_settings_frame,
            corner_radius=0,
            validate="key",
            validatecommand=(self.vcmd_float, "%P"),
            width=40,
            placeholder_text="i.e.: 20",
        )
        self.padding_entry.grid(
            row=0, column=2, sticky="nesw", padx=(0, self.PAD_X), pady=(self.PAD_Y, 0)
        )
        # MarginX settings.
        margin_x_label = ctk.CTkLabel(
            extra_settings_frame, text="MarginX:", font=self.LABEL_FONT
        )
        margin_x_label.grid(
            row=0, column=3, sticky="nes", padx=(0, self.PAD_X), pady=(self.PAD_Y, 0)
        )
        self.margin_x_entry = ctk.CTkEntry(
            extra_settings_frame,
            corner_radius=0,
            validate="key",
            validatecommand=(self.vcmd_float, "%P"),
            width=40,
            placeholder_text="i.e.: 20",
        )
        self.margin_x_entry.grid(
            row=0, column=4, sticky="nesw", padx=(0, self.PAD_X), pady=(self.PAD_Y, 0)
        )
        # MarginY settings.
        marginy_y_label = ctk.CTkLabel(
            extra_settings_frame, text="MarginY:", font=self.LABEL_FONT
        )
        marginy_y_label.grid(
            row=0, column=5, sticky="nes", padx=(0, self.PAD_X), pady=(self.PAD_Y, 0)
        )
        self.margin_y_entry = ctk.CTkEntry(
            extra_settings_frame,
            corner_radius=0,
            validate="key",
            validatecommand=(self.vcmd_float, "%P"),
            width=40,
            placeholder_text="i.e.: 20",
        )
        self.margin_y_entry.grid(
            row=0, column=6, sticky="nesw", padx=(0, self.PAD_X), pady=(self.PAD_Y, 0)
        )
        # Threshold settings section.
        threshold_label = ctk.CTkLabel(
            extra_settings_frame, text="Threshold:", font=self.LABEL_FONT
        )
        threshold_label.grid(
            row=0, column=7, sticky="nes", padx=(0, self.PAD_X), pady=(self.PAD_Y, 0)
        )
        self.threshold_entry = ctk.CTkEntry(
            extra_settings_frame,
            corner_radius=0,
            validate="key",
            validatecommand=(self.vcmd_int, "%P"),
            width=35,
            placeholder_text="i.e.: 0",
        )
        self.threshold_entry.grid(row=0, column=8, sticky="nesw", pady=(self.PAD_Y, 0))

        # Tool tips.
        CTkToolTip(self.stamp_path_entry, "The image to stamp on the PDF.")
        CTkToolTip(
            self.input_dir_entry, "The folder that contains all the " + "PDFs to stamp."
        )
        CTkToolTip(
            self.output_dir_entry, "The folder to output the stamped " + "files to."
        )
        CTkToolTip(
            self.append_entry,
            "Add certain text to the end of the file "
            + "name.\ni.e. '_stamped' would result in "
            + "'file.pdf' => 'file_stamped.pdf'",
        )
        CTkToolTip(
            self.padding_entry,
            "The x/y axis spacing between the stamp " + "and the page's text.",
        )
        CTkToolTip(
            self.margin_x_entry,
            "The x-axis spacing of the stamp away " + "from the page left/right edges.",
        )
        CTkToolTip(
            self.margin_y_entry,
            "The y-axis spacing of the stamp away " + "from the page top/bottom edges.",
        )
        CTkToolTip(
            self.threshold_entry,
            "The search threshold for finding an "
            + "empty space to stamp.\n0 = disable",
        )

    def create_selector_section(self, parent, row, text, function):
        """
        Create a file/directory selector section.

        Args:
          parent (ctk.CTkFrame): the parent frame to attach to.
          row (int): the row index of the parent frame.
          text (str): the text label to display for the entry.
          function (callable): a function accepting one ctk.CTkEntry parameter,
              called when the button is clicked.

        Returns:
          ctk.CTkEntry: The entry created for the selector.
        """
        # Selector label.
        label = ctk.CTkLabel(parent, text=f"{text}:", font=self.LABEL_FONT)
        label.grid(row=row, column=0, sticky="nes", pady=(self.PAD_Y, 0))

        # Sub-frame.
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=1, sticky="nesw")
        frame.grid_columnconfigure(0, weight=1)

        # Path entry.
        entry = ctk.CTkEntry(
            frame,
            font=self.ENTRY_FONT,
            border_width=0,
            corner_radius=0,
            fg_color=("gray80", "gray20"),
        )
        entry.grid(
            row=0, column=0, sticky="nesw", padx=self.PAD_X, pady=(self.PAD_Y, 0)
        )
        # Selector button.
        button = ctk.CTkButton(
            frame,
            text="Select",
            font=self.BUTTON_FONT,
            width=80,
            command=lambda: function(entry),
        )
        button.grid(row=0, column=1, sticky="nes", pady=(self.PAD_Y, 0))

        return entry

    def create_position_settings(self):
        """Creates the position settings (Stamp Position/Search Direction)."""
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(
            fill="x",
            expand=True,
            padx=self.PAD_X * 2,
            pady=(self.PAD_Y, 0),
            anchor="center",
        )
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(3, weight=1)
        frame.grid_columnconfigure(6, weight=1)

        # Stamp position section.
        pos_label = ctk.CTkLabel(frame, text="Stamp\nPosition", font=self.LABEL2_FONT)
        pos_label.grid(row=0, column=1, sticky="nesw")

        # Stamp position: 3x3 button grid.
        pos_frame = ctk.CTkFrame(frame, fg_color="transparent")
        pos_frame.grid(row=0, column=2, sticky="nesw", padx=(self.PAD_X, 0))
        # Create a 3x3 grid of buttons.
        for i in range(3):
            for j in range(3):
                pos_button = ctk.CTkButton(
                    pos_frame,
                    text="",
                    corner_radius=0,
                    width=28,
                    fg_color="gray",
                    border_width=1,
                    command=lambda b=None: self.update_pos_selection(b),
                )
                pos_button.index = i * 3 + j
                pos_button.configure(
                    command=lambda b=pos_button: self.update_pos_selection(b)
                )
                self.pos_buttons.append(pos_button)
                pos_button.grid(row=i, column=j, sticky="nesw", padx=1, pady=1)
                y_position = ["Top", "", "Bottom"]
                x_position = ["Left", "", "Right"]
                position_hover = " ".join([y_position[i], x_position[j]]).strip()
                if position_hover == "":
                    position_hover = "Center"
                pos_tooltip = (
                    f"The grid position to stamp on the " f"PDF.\n[{position_hover}]"
                )

                CTkToolTip(pos_button, pos_tooltip)
        self.pos_buttons[self.data.start_pos].configure(
            fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"]
        )

        # Search direction label.
        dir_label = ctk.CTkLabel(frame, text="Search\nDirection", font=self.LABEL2_FONT)
        dir_label.grid(row=0, column=4, sticky="nesw")
        # Search direction buttons.
        dir_frame = ctk.CTkFrame(frame, fg_color="transparent")
        dir_frame.grid(row=0, column=5, sticky="nesw", padx=(self.PAD_X, 0))
        # Create a 3x3 grid of buttons.
        for i in range(3):
            for j in range(3):
                dir_button = ctk.CTkButton(
                    dir_frame,
                    text="",
                    corner_radius=0,
                    width=36,
                    fg_color="gray",
                    border_width=1,
                    command=lambda b=None: self.update_pos_selection(b),
                )
                dir_button.index = i * 3 + j
                dir_button.configure(
                    command=lambda b=dir_button: self.update_dir_selection(b)
                )
                self.dir_buttons.append(dir_button)
                dir_button.grid(row=i, column=j, sticky="nesw", padx=1, pady=1)
                CTkToolTip(
                    dir_button,
                    "The direction to search for an empty spot "
                    + "to stamp.\nthreshold = 0 to turn off search",
                )
        # Default search: upwards.
        self.dir_buttons[self.data.search_dir].configure(
            fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"]
        )
        # Center button text.
        self.dir_buttons[1].configure(text="Up", font=self.BUTTON2_FONT)
        self.dir_buttons[3].configure(text="Left", font=self.BUTTON2_FONT)
        self.dir_buttons[4].configure(text="All", font=self.BUTTON2_FONT)
        self.dir_buttons[5].configure(text="Right", font=self.BUTTON2_FONT)
        self.dir_buttons[7].configure(text="Down", font=self.BUTTON2_FONT)

    def create_output_section(self):
        """Create the Stamper output section of the UI."""
        # Output section.
        stamper_label = ctk.CTkLabel(
            self,
            text="PDF Stamper",
            font=self.SECTION_FONT,
            fg_color=("gray70", "gray30"),
        )
        stamper_label.pack(fill="x", pady=(self.PAD_Y, 0))
        # Stamper frame.
        stamper_frame = ctk.CTkFrame(self, fg_color="transparent")
        stamper_frame.pack(fill="both", expand=True)
        # Start button.
        self.start_btn = ctk.CTkButton(
            stamper_frame,
            text="Start",
            font=self.BUTTON_FONT,
            command=self.start_stamper,
        )
        self.start_btn.pack(pady=(self.PAD_Y, 0))
        # Progress bar.
        self.progress_bar = ctk.CTkProgressBar(
            stamper_frame, orientation="horizontal", height=self.PAD_Y, corner_radius=0
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=(self.PAD_Y, 0), fill="x")
        # ExtFix output.
        self.stamper_output = ctk.CTkTextbox(stamper_frame, state="disabled")
        self.stamper_output.pack(fill="both", expand=True)

    def start_stamper(self):
        """Starts the stamping process"""
        # Clear the output.
        self.clear_output()
        # Grab values from entries.
        self.data.stamp_path = Path(self.stamp_path_entry.get())
        self.data.input_dir = Path(self.input_dir_entry.get())
        self.data.output_dir = Path(self.output_dir_entry.get())
        self.data.append = self.append_entry.get()
        self.data.padding = self.padding_entry.get().strip()
        self.data.margin_x = self.margin_x_entry.get().strip()
        self.data.margin_y = self.margin_y_entry.get().strip()
        self.data.threshold = self.threshold_entry.get().strip()
        # Validate values.
        if self.data.padding == "":
            self.data.padding = 0
            self.edit_entry(self.padding_entry, "0")
        if self.data.margin_x == "":
            self.data.margin_x = 0
            self.edit_entry(self.margin_x_entry, "0")
        if self.data.margin_y == "":
            self.data.margin_y = 0
            self.edit_entry(self.margin_y_entry, "0")
        if self.data.threshold == "":
            self.data.threshold = 0
            self.edit_entry(self.threshold_entry, "0")

        try:
            self.data.padding = float(self.data.padding)
            self.data.margin_x = float(self.data.margin_x)
            self.data.margin_y = float(self.data.margin_y)
            self.data.threshold = int(self.data.threshold)
        except ValueError:
            self.send_output(
                f"[ERROR] padding: {self.data.padding}, marginX: "
                + f"{self.data.margin_x}, marginY: {self.data.margin_y}, "
                + f"or threshold: {self.data.threshold} is invalid.",
                "error",
            )
            return

        if not self.data.input_dir.exists():
            self.send_output(
                f"[ERROR] '{self.data.input_dir}' directory cant be found.",
                "error",
            )
            return

        # Save the settings locally to a json file.
        self.data.save_config()

        # Lock the button so the user can't press until the process is done.
        self.start_btn.configure(state="disabled")

        # Run the program using a thread.
        thread = threading.Thread(
            target=self.run_stamper_thread,
            args=(self.data.input_dir, self.data.output_dir, self.data.append),
            daemon=True,
        )
        thread.start()

    def run_stamper_thread(self, input_dir, output_dir, append_value):
        """
        The stamper worker thread.

        Args:
          input_dir (Path): The input directory's path.
          output_dir (Path): The output directory's path.
          append_value (str): The value to append to the file name.
        """

        processor = PDFProcessor(
            self.data,
            output_callback=self.send_output,
            progress_callback=lambda p: self.after(0, lambda: self.progress_bar.set(p)),
        )

        success_count, warning_count, error_count = processor.run(
            input_dir, output_dir, append_value
        )

        self.after(
            0, lambda: self.finalize_stamper(success_count, warning_count, error_count)
        )

    def finalize_stamper(self, success_count, warning_count, error_count):
        """
        Send results and unlock the button.

        Args:
          success_count (int): The amount of successful stamps.
          warning_count (int): The amount of files skipped.
          error_count (int): The amount of files failed.
        """
        # Run has finished.
        self.send_output(
            f"Finished stamping {success_count} files with "
            f"{warning_count} skipped and {error_count} errors.",
            "success",
            False,
        )
        self.stamper_output.see("end")

        # Unlock button; process is finished.
        self.start_btn.configure(state="normal")

    def browse_directory(self, entry):
        """
        Open a system folder picker and update the input_dir_entry field.

        Args:
          entry (ctk.CTkEntry): The entry box to fill with the folder's path.
        """
        directory_path = filedialog.askdirectory()
        if directory_path:
            self.edit_entry(entry, directory_path)

    def browse_file(self, entry):
        """
        Open a system file picker and update the stamp_path_entry field.

        Args:
          entry (ctk.CTkEntry): The entry box to fill with the file's path.
        """
        file_path = filedialog.askopenfilename()
        if file_path:
            self.edit_entry(entry, file_path)

    def edit_entry(self, entry, value):
        """
        Edits an entry's value.

        Args:
          entry (ctk.Entry): The entry to edit.
          value (str): The value to set the entry to.
        """
        # Clear the entry.
        entry.delete(0, "end")
        # Insert selected path.
        entry.insert(0, value)

    def clear_output(self):
        """Clear the stamper_output log."""
        # Unlock the output.
        self.stamper_output.configure(state="normal")

        # Delete all the output from line 1, character 0 to the end.
        self.stamper_output.delete("1.0", "end")

        # Lock the output.
        self.stamper_output.configure(state="disabled")

    def send_output(self, output_message, tag=None, endl=True):
        """
        Send a message to the stamper_output log.

        Args:
          output_message (str): The message to send.
          tag (str): Tag to determine message color (default: None).
          endl (bool): End the line or not (default: True).
        """
        # Unlock the output.
        self.stamper_output.configure(state="normal")

        if tag:
            # Send the output with specified tag color.
            self.stamper_output.insert("end", output_message, tag)
        else:
            # Send the output normally.
            self.stamper_output.insert("end", output_message)

        # End the line.
        if endl:
            self.stamper_output.insert("end", "\n")

        # Lock the output.
        self.stamper_output.configure(state="disabled")

    def validate_float(self, value):
        """
        Checks if the user's input is a valid float.

        Args:
          value (str): the user's input to check.

        Returns:
          bool: True if the value is a valid float, False otherwise.
        """
        if value == "":
            return True
        try:
            float(value)
            return True
        except ValueError:
            return False

    def validate_int(self, value):
        """
        Checks if the user's input is a valid int.

        Args:
          value (str): the user's input to check.

        Returns:
          bool: True if the value is a valid int, False otherwise.
        """
        if value == "":
            return True
        try:
            int(value)
            return True
        except ValueError:
            return False

    def update_pos_selection(self, clicked_button):
        """
        Updates the position selector grid.

        Args:
          clicked_button (ctk.CTkButton): The button that was clicked.
        """
        # Adjust color accordingly.
        default_blue = ctk.ThemeManager.theme["CTkButton"]["fg_color"]

        for button in self.pos_buttons:
            button.configure(fg_color="gray")

        clicked_button.configure(fg_color=default_blue)
        self.data.start_pos = clicked_button.index

    def update_dir_selection(self, clicked_button):
        """
        Updates the direction selector grid.

        Args:
          clicked_button (ctk.CTkButton): The button that was clicked.
        """
        # Adjust color accordingly.
        default_blue = ctk.ThemeManager.theme["CTkButton"]["fg_color"]

        for button in self.dir_buttons:
            button.configure(fg_color="gray")

        clicked_button.configure(fg_color=default_blue)
        self.data.search_dir = clicked_button.index

    def populate_ui(self):
        """Populates the UI entries with the current data settings."""
        self.edit_entry(self.stamp_path_entry, str(self.data.stamp_path))
        self.edit_entry(self.input_dir_entry, str(self.data.input_dir))
        self.edit_entry(self.output_dir_entry, str(self.data.output_dir))
        self.edit_entry(self.append_entry, self.data.append)
        self.edit_entry(self.padding_entry, str(self.data.padding))
        self.edit_entry(self.margin_x_entry, str(self.data.margin_x))
        self.edit_entry(self.margin_y_entry, str(self.data.margin_y))
        self.edit_entry(self.threshold_entry, str(self.data.threshold))


def main():
    """The stamper program."""
    app = StamperApp()
    app.mainloop()


if __name__ == "__main__":
    main()
