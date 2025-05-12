# PH Flag Finder

Flag finder for Zelda: PH

## Setup

### Windows

Microsoft's Visual C++ Redistributable is required.

Install the required components:

```bash
python -m pip install -r requirements.txt
```

### Ubuntu/Debian


Install Tkinter (if not installed):

```bash
sudo apt install python3-tk
```

Create a virtual environment (optional but recommended):

```bash
python3 -m venv venv
source venv/bin/activate  # Activate it
```

Install the required components:

```bash
pip install -r requirements.txt
```

## Running PHFF

Run the program like so:

```bash
python phff.py [rom_path]
```

The `rom_path` arg is optional. If omitted, a file dialog window will automatically pop up.

> The ROM must be Zelda: PH. Only US (E) and European (P) versions are supported for now.

## Linting and type-checking

```bash
pip install mypy
pip install pre-commit
```

### Lint

```bash
pre-commit run --all-files
```

### Type-check

```bash
mypy .
```

Python version: 3.12
