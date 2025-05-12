# PH Path Finder

## Setup

### Windows

```bash
python -m pip install -r requirements.txt  # Install required components
python phff.py  # Run the program
```

### Ubuntu/Debian

```bash
sudo apt install python3-tk  # Install tkinter (if not installed)

python3 -m venv venv  # Create a virtual environement (optional but recommended)
source venv/bin/activate  # Activate it

pip install -r requirements.txt  # Install required components
python phff.py  # Run the program
```

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


> Python 3.12
