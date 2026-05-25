# Detect OS for path separators and commands
ifeq ($(OS),Windows_NT)
    SEP := ;
    PYTHON := python
    RM := rmdir /s /q
    DEL := del /f /q
else
    SEP := :
    PYTHON := python3
    RM := rm -rf
    DEL := rm -f
endif

.PHONY: install install-dev gui cli clean

# --- Setup ---
install:
	$(PYTHON) -m pip install -e .
install-dev:
	$(PYTHON) -m pip install -e .[dev]

# --- GUI Builds ---
gui:
ifeq ($(OS),Windows_NT)
	pyinstaller --noconfirm --onefile --windowed \
		--icon=".assets/app/icon.ico" \
		--add-data ".assets/app/icon.png$(SEP)." \
		--add-data ".assets/app/icon.ico$(SEP)." \
		--paths src \
		--name "pdf-stamper-win" src/pdf_stamper/stamper.py
else
	pyinstaller --noconfirm --onefile \
		--add-data ".assets/app/icon.png$(SEP)." \
		--hidden-import PIL._tkinter_finder \
		--paths src \
		--name "pdf-stamper-unix" src/pdf_stamper/stamper.py
endif

# --- CLI Builds ---
cli:
ifeq ($(OS),Windows_NT)
	pyinstaller --noconfirm --onefile \
		--icon=".assets/app/icon.ico" \
		--add-data ".assets/app/icon.png$(SEP)." \
		--add-data ".assets/app/icon.ico$(SEP)." \
		--paths src \
		--name "pdf-stamper-cli-win" src/pdf_stamper/cli.py
else
	pyinstaller --noconfirm --onefile \
		--add-data ".assets/app/icon.png$(SEP)." \
		--hidden-import PIL._tkinter_finder \
		--paths src \
		--name "pdf-stamper-cli-unix" src/pdf_stamper/cli.py
endif

# --- Cleanup ---
clean:
ifeq ($(OS),Windows_NT)
	@if exist build $(RM) build
	@if exist dist $(RM) dist
	@if exist *.spec $(DEL) *.spec
else
	$(RM) build dist *.spec
endif
