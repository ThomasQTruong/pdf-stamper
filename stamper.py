"""Mass stamps files in a specified folder with a specified stamp img.

  This program iterates through a specified input directory and stamps
  all files with a specified stamp file and outputs it into a specified
  output directory.
"""

import os
import pymupdf
import sys
import threading
import customtkinter as ctk
from CTkToolTip import CTkToolTip
from CTkMessagebox import CTkMessagebox
from tkinter import filedialog
from pathlib import Path
from PIL import Image, ImageTk


def get_resource_path(rel_path):
  """Get absolute path to resource for dev and PyInstaller."""
  try:
    base_path = sys._MEIPASS  # pylint: disable=protected-access
  except AttributeError:
    base_path = os.path.abspath(".")
  return os.path.join(base_path, rel_path)


class StamperApp(ctk.CTk):
  """
  A CustomTkinter-based GUI application for mass-stamping pdf files.

  This class inherits from the CustomTkinter class, creates the UI layout,
  and handles the file renaming logic with a visual progress bar.

  Attributes:
    stamp_path_entry (ctk.CTkEntry): Display, shows the selected stamp file
        path (default: ./stamp.png).
    input_dir_entry (ctk.CTkEntry): Display, shows the selected input directory
        (default: ./docs/).
    output_dir_entry (ctk.CTkEntry): Input field, the directory to output the
        stamped file to (default: ./output/).
    append_entry (ctk.CTkEntry): Input field, the string to append to the output
        file.
    threshold_entry (ctk.CTkEntry): Input field, the search threshold for
        finding a whitespace to stamp (default: 1, disable = 0).
    margin_x_entry (ctk.CTkEntry): Input field, the x-axis spacing of the stamp
        away from the page left/right edges.
    margin_y_entry (ctk.CTkEntry): Input field, the y-axis spacing of the stamp
        away from the page top/bottom edges.
    pos_buttons (list[ctk.CTkButton]): A collection of 9 buttons representing
        the stamp position grid.
    dir_buttons (list[ctk.CTkButton]): A collection of 9 buttons representing
        the search directions grid.
    start_btn (ctk.CTkButton): Control, triggers the renaming task.
    progress_bar (ctk.CTkProgressBar): Display, shows the progress of the task.
    stamper_output (ctk.CTkTextbox): Display, shows the task log warnings,
        errors, and completion messages.
    icon (ImageTk.PhotoImage): The app icon.
  """

  # App constants.
  FONT_FAMILY = "Roboto"
  SECTION_FONT = (FONT_FAMILY, 18, "bold")
  LABEL_FONT = (FONT_FAMILY, 16)  # Single-line.
  LABEL2_FONT = (FONT_FAMILY, 12)  # Multi-line / sub-header.
  BUTTON_FONT = (FONT_FAMILY, 14, "bold")   # Normal button.
  BUTTON2_FONT = (FONT_FAMILY, 10, "bold")  # Small button.
  PAD_X = 7  # X-axis padding.
  PAD_Y = 7  # Y-axis padding.
  DEFAULT_INPUT_DIR = "docs"
  DEFAULT_OUTPUT_DIR = "output"
  DEFAULT_STAMP_PATH = "stamp.png"

  # App settings.
  stamp = None
  margin_x = 20
  margin_y = 20
  threshold = 1
  start_pos = 8   # Starting position, default: bottom right (3x3 grid index).
  search_dir = 1  # Search direction, default: upwards (3x3 grid index).
  progress = 0    # The progress of the app.


  def __init__(self):
    """Initialize the application window and build the UI layout."""
    super().__init__()

    # App settings.
    self.title("PDF Stamper")           # Set the title of the app.
    self.geometry("600x400")            # Set app size.
    self.resizable(0, 0)                # Make app unresizeable.
    self.after(200, self.set_app_icon)  # Set the app icon.

    # Data storage.
    self.stamp_path_entry = None
    self.input_dir_entry = None
    self.output_dir_entry = None
    self.append_entry = None
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
    self.vcmd_int   = self.register(self.validate_int)

    # App creation.
    self.create_settings_section()
    self.create_position_settings()
    self.create_output_section()

    # Create color tags for the text output.
    self.stamper_output.tag_config("error", foreground="#cb3f3f")   # Red
    self.stamper_output.tag_config("warning", foreground="#cf8b0c") # Orange
    self.stamper_output.tag_config("success", foreground="#3e9b59") # Green


  def set_app_icon(self):
    """Sets the app icon."""
    try:
      # Obtain path to icon and set it.
      icon_path = get_resource_path("icon.png")
      if not os.path.exists(icon_path):
        icon_path = get_resource_path(os.path.join(".assets", "app",
                                                   "icon.png"))
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
    settings_label = ctk.CTkLabel(self, text="Settings",
                             font=self.SECTION_FONT,
                             fg_color=("gray70", "gray30"))
    settings_label.pack(fill="x")
    # Settings frame.
    settings_frame = ctk.CTkFrame(self, fg_color="transparent")
    settings_frame.pack(fill="x", expand=True, padx=self.PAD_X*2)
    settings_frame.grid_columnconfigure(0, uniform="left")
    settings_frame.grid_columnconfigure(1, weight=1)
    settings_frame.grid_columnconfigure(4)

    # Stamp path frame.
    self.stamp_path_entry = self.create_selector_section(settings_frame,
                                            0, "Stamp", self.browse_file)
    # Input directory frame.
    self.input_dir_entry = self.create_selector_section(settings_frame,
                                      1, "Input", self.browse_directory)
    # Output directory frame.
    self.output_dir_entry = self.create_selector_section(settings_frame,
                                      2, "Output", self.browse_directory)

    # Append section.
    append_label = ctk.CTkLabel(settings_frame, text="Append:",
                                font=self.LABEL_FONT)
    append_label.grid(row=3, column=0, sticky="nesw", pady=(self.PAD_Y, 0))

    extra_settings_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
    extra_settings_frame.grid(row=3, column=1, sticky="nesw")
    extra_settings_frame.grid_columnconfigure(0, weight=1)
    self.append_entry = ctk.CTkEntry(extra_settings_frame, corner_radius=0,
                                     placeholder_text="i.e. _stamped")
    self.append_entry.grid(row=0, column=0, sticky="nesw",
                           padx=self.PAD_X, pady=(self.PAD_Y, 0))
    # MarginX settings.
    margin_x_label = ctk.CTkLabel(extra_settings_frame, text="MarginX:",
                                font=self.LABEL_FONT)
    margin_x_label.grid(row=0, column=1, sticky="nes",
                        padx=(0, self.PAD_X), pady=(self.PAD_Y, 0))
    self.margin_x_entry = ctk.CTkEntry(extra_settings_frame, corner_radius=0,
                        validate="key", validatecommand=(self.vcmd_float, "%P"),
                        width=50, placeholder_text="i.e.: 20")
    self.margin_x_entry.grid(row=0, column=2, sticky="nesw",
                             padx=(0, self.PAD_X), pady=(self.PAD_Y, 0))
    # MarginY settings.
    marginy_y_label = ctk.CTkLabel(extra_settings_frame, text="MarginY:",
                                font=self.LABEL_FONT)
    marginy_y_label.grid(row=0, column=3, sticky="nes",
                         padx=(0, self.PAD_X), pady=(self.PAD_Y, 0))
    self.margin_y_entry = ctk.CTkEntry(extra_settings_frame, corner_radius=0,
                        validate="key", validatecommand=(self.vcmd_float, "%P"),
                        width=50, placeholder_text="i.e.: 20")
    self.margin_y_entry.grid(row=0, column=4, sticky="nesw",
                             padx=(0, self.PAD_X), pady=(self.PAD_Y, 0))
    # Threshold settings section.
    threshold_label = ctk.CTkLabel(extra_settings_frame, text="Threshold:",
                                   font=self.LABEL_FONT)
    threshold_label.grid(row=0, column=5, sticky="nes",
                         padx=(0, self.PAD_X), pady=(self.PAD_Y, 0))
    self.threshold_entry = ctk.CTkEntry(extra_settings_frame, corner_radius=0,
                          validate="key", validatecommand=(self.vcmd_int, "%P"),
                          width=50, placeholder_text="i.e.: 0")
    self.threshold_entry.grid(row=0, column=6, sticky="nesw",
                              pady=(self.PAD_Y, 0))

    # Tool tips.
    CTkToolTip(self.stamp_path_entry, "The image to stamp on the PDF.")
    CTkToolTip(self.input_dir_entry, "The folder that contains all the " +
                                     "PDFs to stamp.")
    CTkToolTip(self.output_dir_entry, "The folder to output the stamped " +
                                      "files to.")
    CTkToolTip(self.append_entry, "Add certain text to the end of the file " +
                                  "name.\ni.e. \'_stamped\' would result in " +
                                  "\'file.pdf\' => \'file_stamped.pdf\'")
    CTkToolTip(self.margin_x_entry, "The x-axis spacing of the stamp away " +
                                    "from the page left/right edges.")
    CTkToolTip(self.margin_y_entry, "The y-axis spacing of the stamp away " +
                                    "from the page top/bottom edges.")
    CTkToolTip(self.threshold_entry, "The search threshold for finding an " +
                                     "empty space to stamp.\n0 = disable")

    # Default values.
    self.stamp_path_entry.insert(0, Path.cwd() / self.DEFAULT_STAMP_PATH)
    self.input_dir_entry.insert(0, Path.cwd() / self.DEFAULT_INPUT_DIR)
    self.output_dir_entry.insert(0, Path.cwd() / self.DEFAULT_OUTPUT_DIR)
    self.margin_x_entry.insert(0, self.margin_x)
    self.margin_y_entry.insert(0, self.margin_y)
    self.threshold_entry.insert(0, self.threshold)


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
    entry = ctk.CTkEntry(frame, font=self.LABEL_FONT,
                         border_width=0, corner_radius=0,
                         fg_color=("gray80", "gray20"))
    entry.grid(row=0, column=0, sticky="nesw",
                padx=self.PAD_X, pady=(self.PAD_Y, 0))
    # Selector button.
    button = ctk.CTkButton(frame, text="Select", font=self.BUTTON_FONT,
                           width=80, command=lambda: function(entry))
    button.grid(row=0, column=1, sticky="nes", pady=(self.PAD_Y, 0))

    return entry


  def create_position_settings(self):
    """Creates the position settings (Stamp Position/Search Direction)."""
    frame = ctk.CTkFrame(self, fg_color="transparent")
    frame.pack(fill="x", expand=True, padx=self.PAD_X*2,
               pady=(self.PAD_Y, 0), anchor="center")
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_columnconfigure(3, weight=1)
    frame.grid_columnconfigure(6, weight=1)

    # Stamp position section.
    pos_label = ctk.CTkLabel(frame, text="Stamp\nPosition",
                        font=self.LABEL2_FONT)
    pos_label.grid(row=0, column=1, sticky="nesw")

    # Stamp position: 3x3 button grid.
    pos_frame = ctk.CTkFrame(frame, fg_color="transparent")
    pos_frame.grid(row=0, column=2, sticky="nesw",
                   padx=(self.PAD_X, 0))
    # Create a 3x3 grid of buttons.
    for i in range(3):
      for j in range(3):
        pos_button = ctk.CTkButton(pos_frame, text="", corner_radius=0,
                            width=28, fg_color="gray", border_width=1,
                            command=lambda b=None: self.update_pos_selection(b))
        pos_button.index = i * 3 + j
        pos_button.configure(command=lambda b=pos_button:
                             self.update_pos_selection(b))
        self.pos_buttons.append(pos_button)
        pos_button.grid(row=i, column=j, sticky="nesw", padx=1, pady=1)
    self.pos_buttons[self.start_pos].configure(fg_color=ctk.ThemeManager
                                    .theme["CTkButton"]["fg_color"])

    # Search direction label.
    dir_label = ctk.CTkLabel(frame, text="Search\nDirection",
                        font=self.LABEL2_FONT)
    dir_label.grid(row=0, column=4, sticky="nesw")
    # Search direction buttons.
    dir_frame = ctk.CTkFrame(frame, fg_color="transparent")
    dir_frame.grid(row=0, column=5, sticky="nesw",
                   padx=(self.PAD_X, 0))
    # Create a 3x3 grid of buttons.
    for i in range(3):
      for j in range(3):
        dir_button = ctk.CTkButton(dir_frame, text="", corner_radius=0,
                            width=32, fg_color="gray", border_width=1,
                            command=lambda b=None: self.update_pos_selection(b))
        dir_button.index = i * 3 + j
        dir_button.configure(command=lambda b=dir_button:
                             self.update_dir_selection(b))
        self.dir_buttons.append(dir_button)
        dir_button.grid(row=i, column=j, sticky="nesw", padx=1, pady=1)
    # Default search: upwards.
    self.dir_buttons[self.search_dir].configure(fg_color=ctk.ThemeManager
                                     .theme["CTkButton"]["fg_color"])
    # Center button text.
    self.dir_buttons[1].configure(text="Up", font=self.BUTTON2_FONT)
    self.dir_buttons[3].configure(text="Left", font=self.BUTTON2_FONT)
    self.dir_buttons[4].configure(text="All", font=self.BUTTON2_FONT)
    self.dir_buttons[5].configure(text="Right", font=self.BUTTON2_FONT)
    self.dir_buttons[7].configure(text="Down", font=self.BUTTON2_FONT)


  def create_output_section(self):
    """Create the Stamper output section of the UI."""
    # Output section.
    stamper_label = ctk.CTkLabel(self, text="PDF Stamper",
                                 font=self.SECTION_FONT,
                                 fg_color=("gray70", "gray30"))
    stamper_label.pack(fill="x", pady=(self.PAD_Y, 0))
    # Stamper frame.
    stamper_frame = ctk.CTkFrame(self, fg_color="transparent")
    stamper_frame.pack(fill="both", expand=True)
    # Start button.
    self.start_btn = ctk.CTkButton(stamper_frame, text="Start",
                                     font=self.BUTTON_FONT,
                                     command=self.start_stamper)
    self.start_btn.pack(pady=(self.PAD_Y, 0))
    # Progress bar.
    self.progress_bar = ctk.CTkProgressBar(stamper_frame,
                                           orientation="horizontal",
                                           height=self.PAD_Y, corner_radius=0)
    self.progress_bar.set(0)
    self.progress_bar.pack(pady=(self.PAD_Y, 0), fill="x")
    # ExtFix output.
    self.stamper_output = ctk.CTkTextbox(stamper_frame, state="disabled")
    self.stamper_output.pack(fill="both", expand=True)


  def start_stamper(self):
    """Starts the stamping process"""
    self.clear_output()
    # Grab values from entries.
    self.stamp = Path(self.stamp_path_entry.get())
    input_dir = Path(self.input_dir_entry.get())
    output_dir = Path(self.output_dir_entry.get())
    append_value = self.append_entry.get()
    self.margin_x = self.margin_x_entry.get().strip()
    self.margin_y = self.margin_y_entry.get().strip()
    self.threshold = self.threshold_entry.get().strip()
    # Validate values.
    if self.margin_x == "":
      self.margin_x = 0
      self.edit_entry(self.margin_x_entry, "0")
    if self.margin_y == "":
      self.margin_y = 0
      self.edit_entry(self.margin_y_entry, "0")
    if self.threshold == "":
      self.threshold = 0
      self.edit_entry(self.threshold_entry, "0")

    try:
      self.margin_x = float(self.margin_x)
      self.margin_y = float(self.margin_y)
      self.threshold = int(self.threshold)
    except ValueError:
      self.send_output(f"[ERROR] marginX: {self.margin_x}, marginY: " +
                       f"{self.margin_y}, or threshold: {self.threshold} " +
                       "is invalid.", "error")
      return

    if not input_dir.exists():
      self.send_output(f"[ERROR] \'{input_dir.name}\' directory cant be found.",
                       "error")
      return

    # Lock the button so the user can't press until the process is done.
    self.start_btn.configure(state="disabled")

    # Run the program using a thread.
    thread = threading.Thread(
      target=self.run_stamper_thread,
      args=(input_dir, output_dir, append_value),
      daemon=True
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
    # Counters
    success_count = 0
    warning_count = 0
    error_count = 0

    # For each pdf in the target directory.
    self.progress = 0
    for pdf in input_dir.iterdir():
      # Going through the file, add 1 to progress.
      self.progress += 1

      # If it is not a file, skip it.
      if not pdf.is_file():
        warning_count += 1
        self.send_output(f"[WARNING] {pdf.name}: skipped, not a valid file.",
                         "warning")
        continue

      # Grab output directory and create if it doesnt exist.
      output_dir.mkdir(parents=True, exist_ok=True)

      # Customize the output name.
      output_name = pdf.stem + append_value + pdf.suffix
      output_pdf = output_dir / output_name

      # Add the stamp to the pdf.
      success = self.add_stamp(pdf, output_pdf)
      if success == 1:
        # Returned 1, there was an error.
        error_count += 1
      elif success == 2:
        # Returned 2, there was a warning.
        warning_count += 1
      else:
        success_count += 1
    self.after(0, lambda: self.finalize_stamper(success_count, warning_count,
                                                error_count))


  def finalize_stamper(self, success_count, warning_count, error_count):
    """
    Send results and unlock the button.

    Args:
      success_count (int): The amount of successful stamps.
      warning_count (int): The amount of files skipped.
      error_count (int): The amount of files failed.
    """
    # Run has finished.
    self.send_output(f"Finished stamping {success_count} files with "
                     f"{warning_count} skipped and {error_count} errors.",
                     "success", False)
    self.stamper_output.see("end")

    # Unlock button; process is finished.
    self.start_btn.configure(state="normal")


  def add_stamp(self, input_pdf, output_pdf):
    """
    Adds a stamp to the pdf file.

    Args:
      input_pdf (Path): the input file's path.
      output_pdf (Path): the output file's path.

    Returns:
      int: 0 if success, 1 if error, and 2 if warning.
    """
    # Open the pdf with pymupdf.
    doc = pymupdf.open(input_pdf)
    pages_to_stamp = range(1, len(doc) + 1)
    input_dir = Path(self.input_dir_entry.get())

    try:
      with Image.open(self.stamp) as img:
        stamp_width, stamp_height = img.size
    except FileNotFoundError:
      self.send_output(f"[Error] \'{self.stamp}\' is missing!", "error")
      return 1

    for page_num in pages_to_stamp:
      # Amount of items in the directory (for progress bar).
      progress_total = self.get_progress_total(input_dir)

      # Update progress.
      self.progress += 1
      self.after(0, lambda p=self.progress / progress_total:
                 self.progress_bar.set(p))

      # PDF page indices start at 0.
      page = doc[page_num - 1]

      # Obtain page dimensions and top-left values.
      br = page.rect.br
      x0 = self.margin_x
      y0 = self.margin_y
      x1 = x0 + stamp_width
      y1 = y0 + stamp_height
      start_row = int(self.start_pos / 3)
      start_column = self.start_pos % 3

      # Set x-value based on column.
      if start_column == 1:
        # Middle column, center the stamp.
        x0 = (br.x - stamp_width) / 2
        x1 = x0 + stamp_width
      elif start_column == 2:
        # Right column.
        x0 = br.x - self.margin_x - stamp_width
        x1 = br.x - self.margin_x

      # Set y-value based on row.
      if start_row == 1:
        # Middle row.
        y0 = (br.y - stamp_height) / 2
        y1 = y0 + stamp_height
      elif start_row == 2:
        # Bottom row.
        y0 = br.y - self.margin_y - stamp_height
        y1 = br.y - self.margin_y

      # Check margin x/y values.
      if self.is_out_of_bounds(x0, x1, br.x, self.margin_x):
        self.send_output(f"[Skipped] Out of Bounds: marginX ({self.margin_x})"
                         f" or stamp width ({stamp_width}) is too high for" +
                         f" the page width ({br.x})!", "warning")
        return 2
      if self.is_out_of_bounds(y0, y1, br.y, self.margin_y):
        self.send_output(f"[Skipped] Out of Bounds: marginY ({self.margin_y})" +
                         f" or stamp height ({stamp_height}) is too high for" +
                         f" the page height ({br.y})!", "warning")
        return 2

      rect = pymupdf.Rect(x0, y0, x1, y1)
      # Search is enabled.
      if self.threshold > 0:
        if self.search_dir == 4:
          # Search all of the directions.
          rect = self.search_all(page, rect)
        else:
          # Search normally.
          rect = self.search(page, rect)

      page.insert_image(rect, filename=self.stamp)

    doc.save(output_pdf)
    doc.close()
    return 0


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
    self.start_pos = clicked_button.index


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
    self.search_dir = clicked_button.index

    # Selected all directions and has very low threshold.
    if clicked_button.index == 4 and self.threshold < 25:
      CTkMessagebox(title="Warning",
                    message="Threshold is low (< ~25) for searching all" +
                            "directions. It will probably take a long" + 
                            "time to search.",
                    icon="warning",
                    option_1 = "OK",
                    master=self)


  def is_out_of_bounds(self, pos0, pos1, max_size, margin):
    """
    Determines whether the box coordinates are outside of the page bound.
    
    Args:
      pos0 (float): the x0/y0 coordinate of the box.
      pos1 (float): the x1/y1 coordinate of the box.
      max_size (float): the page height/width.
      margin (int): the inner-distance away from the edge.
    
    Returns:
      bool: True if the rect is out of bounds, False otherwise.
    """
    return pos0 < margin or pos1 > max_size - margin


  def search(self, page, rect):
    """
    Searches for an empty spot to stamp at the selected direction.

    Args:
      page (Page): The document page to search on.
      rect (pymupdf.Rect): The rectangle where the stamp goes.
    
    Returns:
      pymupdf.Rect: The rect with the found position, else original rect.
    """
    text_in_rect = page.get_text("text", clip=rect)
    # Empty spot at the location already.
    if not text_in_rect.strip():
      return rect
    br = page.rect.br
    search_row = int(self.search_dir / 3)
    search_column = self.search_dir % 3

    # Calculate threshold based on direction.
    threshold_x = self.threshold
    if search_column == 0:  # Left column.
      threshold_x *= -1
    elif search_column % 3 == 1:  # Middle column.
      threshold_x = 0

    threshold_y = self.threshold
    if search_row == 0:  # Top row.
      threshold_y *= -1
    elif search_row == 1:  # Middle row.
      threshold_y = 0

    # Diagonal search.
    if self.search_dir % 2 == 0:
      # Figure out the end point to calculate slope.
      stamp_width = rect.x1 - rect.x0
      stamp_height = rect.y1 - rect.y0
      end_x = self.margin_x
      end_y = self.margin_y
      if self.margin_x == rect.x0:
        end_x = br.x - self.margin_x - stamp_width
      if self.margin_y == rect.y0:
        end_y = br.y - self.margin_y - stamp_height

      # Calculate slope with slope formula.
      slope = (end_y - rect.y0) / (end_x - rect.x0)

      # Formula: y = mx + b, so apply slope to threshold_x.
      threshold_x *= slope

    # Search for a free slot using the selected direction.
    temp_x0 = rect.x0
    temp_y0 = rect.y0
    temp_x1 = rect.x1
    temp_y1 = rect.y1
    while text_in_rect.strip():
      temp_x0 += threshold_x
      temp_y0 += threshold_y
      temp_x1 += threshold_x
      temp_y1 += threshold_y
      temp_rect = pymupdf.Rect(temp_x0, temp_y0, temp_x1, temp_y1)
      text_in_rect = page.get_text("text", clip=temp_rect)
      # Search is out of bounds, return original rect.
      if (self.is_out_of_bounds(temp_x0, temp_x1, br.x, self.margin_x) or
          self.is_out_of_bounds(temp_y0, temp_y1, br.y, self.margin_y)):
        return rect

    # Passed through conditions, successfully found spot.
    return temp_rect


  def search_all(self, page, rect):
    """
    Searches for an empty spot to stamp for both x and y axis.

    Args:
      page (Page): The document page to search on.
      rect (pymupdf.Rect): The rectangle where the stamp goes.
    
    Returns:
      pymupdf.Rect: The rect with the found position, else original rect.
    """
    text_in_rect = page.get_text("text", clip=rect)
    # Empty spot at the location already.
    if not text_in_rect.strip():
      return rect
    br = page.rect.br

    # Start from the top-left corner.
    temp_y0 = self.margin_y
    temp_y1 = temp_y0 + rect.y1 - rect.y0

    # While text is in the way and y-axis is not out.
    while text_in_rect.strip():
      temp_x0 = self.margin_x
      temp_x1 = temp_x0 + rect.x1 - rect.x0
      # While while text is in the way in the column.
      while text_in_rect.strip():
        temp_rect = pymupdf.Rect(temp_x0, temp_y0, temp_x1, temp_y1)
        text_in_rect = page.get_text("text", clip=temp_rect)
        # X-axis is out of bounds, check next row.
        if self.is_out_of_bounds(temp_x0, temp_x1, br.x, self.margin_x):
          break
        # Move x/y by the threshold.
        temp_x0 += self.threshold
        temp_x1 += self.threshold
      # Y-axis is out of bounds, return original rect (couldn't find any).
      if self.is_out_of_bounds(temp_y0, temp_y1, br.y, self.margin_y):
        return rect
      temp_y0 += self.threshold
      temp_y1 += self.threshold

    # Passed through conditions, successfully found spot.
    return temp_rect


  def get_progress_total(self, input_dir):
    """
    Retrives the progress total (file count + pages).

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


if __name__ == "__main__":
  app = StamperApp()
  app.mainloop()
