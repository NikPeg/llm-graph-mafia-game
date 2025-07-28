# Installation Guide

## Prerequisites
- Python 3.12 or higher
- Git

## Installation Steps

### Option 1: Using uv (Recommended)
```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync
```

### Option 2: Using pip
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Option 3: Using pip with pyproject.toml
```bash
# Install in development mode
pip install -e .
```

## Verify Installation
```bash
# Test that all modules can be imported
python -c "import dotenv, firebase_admin, flask, matplotlib, numpy, requests; print('All dependencies installed successfully!')"
```

## Common Issues

### "No module named 'dotenv'"
This means python-dotenv is not installed. Try:
```bash
pip install python-dotenv==1.0.0
```

### Firebase credentials missing
Make sure you have `firebase_credentials.json` in the project root.

### Permission errors
On macOS/Linux, you might need to use `python3` instead of `python`:
```bash
python3 -m pip install -r requirements.txt