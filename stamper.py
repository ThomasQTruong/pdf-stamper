"""Mass stamps files in a specified folder with a specified stamp img.

  This program iterates through a specified input directory and stamps
  all files with a specified stamp file and outputs it into a specified
  output directory.
"""

import os
import sys
import pymupdf
import customtkinter as ctk
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
    start_btn (ctk.CTkButton): Control, triggers the renaming task.
    progress_bar (ctk.CTkProgressBar): Display, shows the progress of the task.
    stamper_output (ctk.CTkTextbox): Display, shows the task log warnings,
        errors, and completion messages.
    icon (ImageTk.PhotoImage): The app icon.
  """

  # App constants.
  FONT_FAMILY = "Roboto"
  SECTION_FONT = (FONT_FAMILY, 18, "bold")
  LABEL_FONT = (FONT_FAMILY, 16)
  BUTTON_FONT = (FONT_FAMILY, 14, "bold")
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
    self.start_btn = None
    self.progress_bar = None
    self.stamper_output = None
    self.icon = None

    # Data validators.
    self.vcmd_float = self.register(self.validate_float)
    self.vcmd_int   = self.register(self.validate_int)

    # App creation.
    self.create_settings_section()
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
                                     placeholder_text="i.e.: _stamped")
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


  def create_output_section(self):
    """Create the Stamper output section of the UI."""
    # Output section.
    stamper_label = ctk.CTkLabel(self, text="PDF Stamper",
                                 font=self.SECTION_FONT,
                                 fg_color=("gray70", "gray30"))
    stamper_label.pack(fill="x", pady=(self.PAD_Y*2, 0))
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

    # Counters
    success_count = 0
    warning_count = 0
    error_count = 0

    # Amount of items in the directory (for progress bar).
    item_total = sum(1 for _ in os.scandir(input_dir))

    # For each pdf in the target directory.
    index = 0
    for pdf in input_dir.iterdir():
      # Draw the progress bar (rate limited)!
      index += 1
      if index % 100 == 0 or index == item_total:
        self.progress_bar.set(index/item_total)
        self.update()

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

    # Run has finished.
    self.send_output(f"Finished stamping {success_count} files with "
                     f"{warning_count} skipped and {error_count} errors.",
                     "success", False)
    self.stamper_output.see("end")

    # Unlock button; process is finished.
    self.update()  # Flush the event queue.
    self.start_btn.configure(state="normal")


  def add_stamp(self, input_pdf, output_pdf):
    """
    Adds a stamp to the pdf file.

    input_pdf (Path): the input file's path.
    output_pdf (Path): the output file's path.
    """
    # Open the pdf with pymupdf.
    doc = pymupdf.open(input_pdf)
    pages_to_stamp = range(1, len(doc) + 1)

    try:
      with Image.open(self.stamp) as img:
        stamp_width, stamp_height = img.size
    except FileNotFoundError:
      self.send_output(f"[Error] \'{self.stamp}\' is missing!", "error")
      return 1

    for page_num in pages_to_stamp:
      # PDF page indices start at 0.
      page = doc[page_num - 1]

      # Obtain page dimensions.
      br = page.rect.br
      x0 = br.x - stamp_width - self.margin_x
      y0 = br.y - stamp_height - self.margin_y
      x1 = br.x - self.margin_x
      y1 = br.y - self.margin_y
      temp_rect = pymupdf.Rect(x0, y0, x1, y1)

      # Check margin x/y values.
      if x0 < self.margin_x:
        self.send_output(f"[Warning] marginX ({self.margin_x}) or stamp " +
                         f"width ({stamp_width}) is too high for the page " +
                         f"width of {br.x}!", "warning")
        return 2
      if y0 < self.margin_y:
        self.send_output(f"[Warning] marginY ({self.margin_y}) or stamp " +
                         f"height ({stamp_height}) is too high for the page " +
                         f"height of {br.y}!", "warning")
        return 2

      # CHECK FOR TEXT: search for any text inside that rectangle
      text_in_rect = page.get_text("text", clip=temp_rect)

      # There is text in the way, move up.
      temp_y0 = y0
      temp_y1 = y1
      # Search is enabled.
      if self.threshold > 0:
        while text_in_rect.strip() and temp_y0 > self.margin_y:
          temp_y0 = temp_y0 - self.threshold
          temp_y1 = temp_y1 - self.threshold
          temp_rect = pymupdf.Rect(x0, temp_y0, x1, temp_y1)
          text_in_rect = page.get_text("text", clip=temp_rect)

      # Went out of bounds, default to bottom right.
      if temp_y0 < 0:
        rect = pymupdf.Rect(x0, y0, x1, y1)
      # In bounds, use new coordinates.
      else:
        rect = pymupdf.Rect(x0, temp_y0, x1, temp_y1)

      page.insert_image(rect, filename=self.stamp)

    doc.save(output_pdf)
    doc.close()
    return 0


  def browse_directory(self, entry):
    """Open a system folder picker and update the input_dir_entry field."""
    directory_path = filedialog.askdirectory()
    if directory_path:
      self.edit_entry(entry, directory_path)


  def browse_file(self, entry):
    """Open a system file picker and update the stamp_path_entry field."""
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
    if value == "":
      return True
    try:
      float(value)
      return True
    except ValueError:
      return False

  def validate_int(self, value):
    if value == "":
      return True
    try:
      int(value)
      return True
    except ValueError:
      return False

if __name__ == "__main__":
  app = StamperApp()
  app.mainloop()
