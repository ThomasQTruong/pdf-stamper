# PDF Stamper

Mass stamps files in a specified folder with a specified stamp img.

<p align="center">
  <img src=".assets/docs/stamper-icon.png" width="200" title="PDF Stamper Icon">
</p>

# Requirements

- Only needed for development.
- Python >= 3.9
- ```bash
     pip install -r requirements.txt
  ```

# How To use (GUI - [stamper.py](stamper.py))

1. Download from the [releases](https://github.com/ThomasQTruong/pdf-stamper/releases).
2. Open the program.
   - <img src=".assets/docs/stamper-main.png" width="300" title="PDF Stamper GUI">
3. Select the stamp image (default: `./stamp.png`).
   - <img src=".assets/docs/stamper-file-select.png" width="300" title="PDF Stamper File Selector">
4. Select the input directory (folder that contains all the PDFs to stamp; default: `./docs/`).
   - <img src=".assets/docs/stamper-folder-select.png" width="300" title="PDF Stamper Folder Selector">
5. Enter the other settings or leave default.
   - `Output`: The folder to output the stamped files to (default: `./output/`).
   - `Append`: Add certain text to the end of the file name.
     - i.e. Append = `_stamped` would result in `file.pdf` => `file_stamped.pdf`
   - `MarginX`: The x-axis spacing of the stamp away from the page left/right edges (default: `20`).
   - `MarginY`: The y-axis spacing of the stamp away from the page top/bottom edges (default: `20`).
   - `Threshold`: The search threshold for finding an empty space to stamp (default: `1`).
     - Only stamps on the right side, starts from bottom then searches upward for space.
     - Set to `0` if you do not want it to search for any space; fixed stamp at bottom-right.
   - `Stamp Position`: The position on a 3x3 grid of where to stamp.
   - `Search Direction`: The direction to search for an empty spot to stamp.
6. Click start and the files should be stamped!
   - <img src=".assets/docs/stamper-output.png" width="300" title="PDF Stamper Output">
   - <img src=".assets/docs/stamped-example.png" width="300" title="PDF Stamped">

# Generate Windows .EXE

- Multi-liner
  - ```bash
    pyinstaller --noconfirm --onefile --windowed `
    --icon=".assets/app/icon.ico" `
    --add-data ".assets/app/icon.png;." `
    --add-data ".assets/app/icon.ico;." `
    --name "PDF Stamper" `
    stamper.py
    ```

- One-liner
  - ```bash
    pyinstaller --noconfirm --onefile --windowed --icon=".assets/app/icon.ico" --add-data ".assets/app/icon.png;." --add-data ".assets/app/icon.ico;." --name "PDF Stamper" stamper.py
    ```
