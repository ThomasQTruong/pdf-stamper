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
    stamp_path_entry (ctk.CTkEntry): Display, shows the selected stamp file path.
    input_dir_entry (ctk.CTkEntry): Display, shows the selected input directory.
    output_dir_entry (ctk.CTkEntry): Input field, the directory to output the stamped file to.
    append_entry (ctk.CTkEntry): Input field, the string to append to the output file.
    threshold_entry (ctk.CTkEntry): Input field, the search threshold for finding a whitespace
        to stamp.
    margin_entry (ctk.CTkEntry): Input field, the spacing of the stamp away from the page edges.
    start_btn (ctk.CTkButton): Control, triggers the renaming task.
    progress_bar (ctk.CTkProgressBar): Display, shows the progress of the task.
    stamper_output (ctk.CTkTextbox): Display, shows the task log warnings,
        errors, and completion messages.
    icon (ImageTk.PhotoImage): The app icon.
  """

  # App constants.
  FONT_FAMILY = "Roboto"
  SECTION_FONT = (FONT_FAMILY, 20, "bold")
  LABEL_FONT = (FONT_FAMILY, 18)
  BUTTON_FONT = (FONT_FAMILY, 14, "bold")
  PAD_X = 14  # X-axis padding.
  PAD_Y = 14  # Y-axis padding.
  STAMP = None
  THRESHOLD = None
  MARGFIN = None


  def __init__(self):
    """Initialize the application window and build the UI layout."""
    super().__init__()

    # App settings.
    self.title("PDF Stamper")           # Set the title of the app.
    self.geometry("500x400")            # Set app size.
    self.resizable(0, 0)                # Make app unresizeable.
    self.after(200, self.set_app_icon)  # Set the app icon.

    # Data storage.
    self.stamp_path_entry = None
    self.input_dir_entry = None
    self.output_dir_entry = None
    self.append_entry = None
    self.threshold_entry = None
    self.margin_entry = None
    self.start_btn = None
    self.progress_bar = None
    self.stamper_output = None
    self.icon = None

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
    # Settings section.
    settings_label = ctk.CTkLabel(self, text="Settings",
                             font=self.SECTION_FONT,
                             fg_color=("gray70", "gray30"))
    settings_label.pack(fill="x")
    # Stamp path frame.
    stamp_path_frame = ctk.CTkFrame(self, fg_color="transparent")
    stamp_path_frame.pack(fill="x")
    # Stamp path label.
    stamp_path_label = ctk.CTkLabel(stamp_path_frame, text="Stamp:",
                                    font=self.LABEL_FONT)
    stamp_path_label.pack(padx=(self.PAD_X, self.PAD_X/2),
                          pady=(self.PAD_Y/2, 0), side="left")
    # Stamp path entry.
    self.stamp_path_entry = ctk.CTkEntry(stamp_path_frame, font=self.LABEL_FONT,
                                       border_width=0, corner_radius=0,
                                       fg_color=("gray80", "gray20"))
    self.stamp_path_entry.insert(0, "No File Selected")
    self.stamp_path_entry.configure(state="readonly")
    self.stamp_path_entry.pack(padx=(0, self.PAD_X), pady=(self.PAD_Y/2, 0), fill="x", expand=True)
    # File selector button.
    file_selector_btn = ctk.CTkButton(self, text="Select", font=self.BUTTON_FONT,
                                     command=self.browse_file)
    file_selector_btn.pack(padx=self.PAD_X, pady=(self.PAD_Y/2, 0))

    # Input directory frame.
    input_dir_frame = ctk.CTkFrame(self, fg_color="transparent")
    input_dir_frame.pack(fill="x")
    # Input directory label.
    input_directory_label = ctk.CTkLabel(input_dir_frame, text="Input:",
                                    font=self.LABEL_FONT)
    input_directory_label.pack(padx=(self.PAD_X, self.PAD_X/2),
                          pady=(self.PAD_Y/2, 0), side="left")
    # Input entry label.
    self.input_dir_entry = ctk.CTkEntry(input_dir_frame, font=self.LABEL_FONT,
                                       border_width=0, corner_radius=0,
                                       fg_color=("gray80", "gray20"))
    self.input_dir_entry.insert(0, "No Directory Selected")
    self.input_dir_entry.configure(state="readonly")
    self.input_dir_entry.pack(padx=(0, self.PAD_X), pady=(self.PAD_Y/2, 0), fill="x", expand=True)
    # Directory selector button.
    dir_selector_btn = ctk.CTkButton(self, text="Select", font=self.BUTTON_FONT,
                                     command=self.browse_directory)
    dir_selector_btn.pack(padx=self.PAD_X, pady=(self.PAD_Y/2, 0))

    # Extra settings frame.
    extra_settings_frame = ctk.CTkFrame(self, fg_color="transparent")
    extra_settings_frame.pack(fill="x", expand=True, padx=self.PAD_X, pady=(self.PAD_Y/2, 0))
    extra_settings_frame.grid_columnconfigure(0, weight=1)
    extra_settings_frame.grid_columnconfigure(1, weight=1)
    # Extra - Left frame.
    extra_left_frame = ctk.CTkFrame(extra_settings_frame, fg_color="transparent")
    extra_left_frame.grid(row=0, column=0, sticky="nsw", padx=(0, self.PAD_X))
    # Extra - right frame.
    extra_right_frame = ctk.CTkFrame(extra_settings_frame, fg_color="transparent")
    extra_right_frame.grid(row=0, column=1, sticky="nse")
    # Output directory section.
    output_dir_label = ctk.CTkLabel(extra_left_frame, text="Output:", font=self.LABEL_FONT)
    output_dir_label.grid(row=0, column=0, sticky="nse", padx=(0, self.PAD_X/2))
    self.output_dir_entry = ctk.CTkEntry(extra_left_frame, corner_radius=0,
                                         placeholder_text="example: output")
    self.output_dir_entry.grid(row=0, column=1, sticky="nsew")
    # Append section.
    append_label = ctk.CTkLabel(extra_right_frame, text="Append:", font=self.LABEL_FONT)
    append_label.grid(row=0, column=0, sticky="nse", padx=(0, self.PAD_X/2))
    self.append_entry = ctk.CTkEntry(extra_right_frame, corner_radius=0,
                                     placeholder_text="example: _stamped")
    self.append_entry.grid(row=0, column=1, sticky="nsew")
    # Threshold settings section.
    threshold_label = ctk.CTkLabel(extra_left_frame, text="Threshold:", font=self.LABEL_FONT)
    threshold_label.grid(row=1, column=0, sticky="nse", padx=(0, self.PAD_X/2))
    self.threshold_entry = ctk.CTkEntry(extra_left_frame, corner_radius=0,
                                        placeholder_text="example: 0 (forced)")
    self.threshold_entry.grid(row=1, column=1, sticky="nsew")
    # Margin settings section.
    margin_label = ctk.CTkLabel(extra_right_frame, text="Margin:", font=self.LABEL_FONT)
    margin_label.grid(row=1, column=0, sticky="nse", padx=(0, self.PAD_X/2))
    self.margin_entry = ctk.CTkEntry(extra_right_frame, corner_radius=0,
                                     placeholder_text="example: 20")
    self.margin_entry.grid(row=1, column=1, sticky="nsew")
    
    # Default values.
    self.editLockedEntry(self.stamp_path_entry, "stamp.png")
    self.editLockedEntry(self.input_dir_entry, Path("docs"))
    self.output_dir_entry.insert(0, "output")
    self.threshold_entry.insert(0, 1)
    self.margin_entry.insert(0, 20)


  def start_stamper(self):
    """Starts the stamping process"""
    self.clear_output()
    # Grab values from entries.
    self.STAMP = Path(self.stamp_path_entry.get())
    input_dir = Path(self.input_dir_entry.get())
    output_dir = Path(self.output_dir_entry.get().lower().strip())
    append_value = self.append_entry.get().lower().strip()
    self.THRESHOLD = int(self.threshold_entry.get().strip())
    self.MARGIN = int(self.margin_entry.get().strip())

    if (not input_dir.exists()):
      self.send_output(f"[ERROR] \'{input_dir.name}\' directory cant be found.", "error")
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
      if success:
        # Returned 1, there was an error. 
        error_count = error_count + 1
      else:
        success_count = success_count + 1

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
      with Image.open(self.STAMP) as img:
        stamp_width, stamp_height = img.size
    except FileNotFoundError:
      self.send_output(f"[Error] \'{self.STAMP}\' is missing!", "error")
      return 1

    for page_num in pages_to_stamp:
      # PDF page indices start at 0.
      page = doc[page_num - 1]
      
      # Obtain page dimensions.
      br = page.rect.br
      x0 = br.x - stamp_width - self.MARGIN
      y0 = br.y - stamp_height - self.MARGIN
      x1 = br.x - self.MARGIN
      y1 = br.y - self.MARGIN
      temp_rect = pymupdf.Rect(x0, y0, x1, y1)

      # CHECK FOR TEXT: search for any text inside that rectangle
      text_in_rect = page.get_text("text", clip=temp_rect)

      # There is text in the way, move up.
      temp_y0 = y0
      temp_y1 = y1
      # Search is enabled.
      if self.THRESHOLD > 0:
        while text_in_rect.strip() and temp_y0 > self.MARGIN:
          temp_y0 = temp_y0 - self.THRESHOLD
          temp_y1 = temp_y1 - self.THRESHOLD
          temp_rect = pymupdf.Rect(x0, temp_y0, x1, temp_y1)
          text_in_rect = page.get_text("text", clip=temp_rect)
      
      # Went out of bounds, default to bottom right.
      if temp_y0 < 0:
        rect = pymupdf.Rect(x0, y0, x1, y1)
      # In bounds, use new coordinates.
      else:
        rect = pymupdf.Rect(x0, temp_y0, x1, temp_y1)
      
      page.insert_image(rect, filename=self.STAMP)

    doc.save(output_pdf)
    doc.close()
    return 0


  def create_output_section(self):
    """Create the Stamper output section of the UI."""
    # Output section.
    stamper_label = ctk.CTkLabel(self, text="PDF Stamper", font=self.SECTION_FONT,
                                 fg_color=("gray70", "gray30"))
    stamper_label.pack(fill="x", pady=(self.PAD_Y, 0))
    # Stamper frame.
    stamper_frame = ctk.CTkFrame(self, fg_color="transparent")
    stamper_frame.pack(fill="both", expand=True)
    # Start button.
    self.start_btn = ctk.CTkButton(stamper_frame, text="Start",
                                     font=self.BUTTON_FONT,
                                     command=self.start_stamper)
    self.start_btn.pack(pady=(self.PAD_Y/2, 0))
    # Progress bar.
    self.progress_bar = ctk.CTkProgressBar(stamper_frame,
                                           orientation="horizontal",
                                           height=self.PAD_Y, corner_radius=0)
    self.progress_bar.set(0)
    self.progress_bar.pack(pady=(self.PAD_Y/2, 0), fill="x")
    # ExtFix output.
    self.stamper_output = ctk.CTkTextbox(stamper_frame, state="disabled")
    self.stamper_output.pack(fill="both", expand=True)

  
  def browse_directory(self):
    """Open a system folder picker and update the input_dir_entry field."""
    directory_path = filedialog.askdirectory()
    if directory_path:
      self.editLockedEntry(self.input_dir_entry, directory_path)


  def browse_file(self):
    """Open a system file picker and update the stamp_path_entry field."""
    file_path = filedialog.askopenfilename()
    if file_path:
      self.editLockedEntry(self.stamp_path_entry, file_path)


  def editLockedEntry(self, entry, value):
    """
    Edits a locked entry's value.

    Args:
      entry (ctk.Entry): The locked entry to edit.
      value (str): The value to set the entry to.
    """
    # Unlock the entry.
    entry.configure(state="normal")
    # Clear the entry.
    entry.delete(0, "end")
    # Insert selected path.
    entry.insert(0, value)
    # Lock the entry.
    entry.configure(state="readonly")


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


if __name__ == "__main__":
  app = StamperApp()
  app.mainloop()
